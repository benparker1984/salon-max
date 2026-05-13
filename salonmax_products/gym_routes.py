from __future__ import annotations

import json
import os

from flask import jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from salonmax_products import gym as gym_product


def register_gym_routes(app, deps):
    """Register gym product routes while preserving existing endpoint names."""

    def ensure_default_gym_business():
        return deps["ensure_default_gym_business"]()

    def default_gym_business_public_id():
        return deps["default_gym_business_public_id"]()

    def json_error(code, message, *, status=400):
        return deps["json_error"](code, message, status=status)

    def salonmax_public_gym_snapshot(business_account_public_id):
        return deps["salonmax_public_gym_snapshot"](business_account_public_id)

    def gym_staff_session_key(business_account_public_id):
        return deps["gym_staff_session_key"](business_account_public_id)

    def gym_staff_login_redirect(business_account_public_id):
        return deps["gym_staff_login_redirect"](business_account_public_id)

    def salonmax_gym_surface(business_account_public_id: str, surface: str):
        if business_account_public_id == default_gym_business_public_id():
            ensure_default_gym_business()
        snapshot = salonmax_public_gym_snapshot(business_account_public_id)
        if snapshot is None:
            return json_error("GYM_NOT_FOUND", "No gym signup site was found for that business account.", status=404)
        return render_template(
            "gym_access_portal.html",
            snapshot=snapshot,
            title=f"Join {snapshot['brand_name']}",
            surface=surface,
            notice=request.args.get("notice", "").strip(),
        )

    @app.route("/kado")
    def kado_public_gym_site():
        if not gym_product.friendly_shortcuts_enabled():
            return json_error("SHORTCUT_DISABLED", "This gym shortcut is disabled for this deployment.", status=404)
        business_account_public_id = ensure_default_gym_business()
        return redirect(url_for("salonmax_public_gym_site", business_account_public_id=business_account_public_id))

    @app.route("/gym")
    def default_gym_public_site():
        if not gym_product.friendly_shortcuts_enabled():
            return json_error("SHORTCUT_DISABLED", "This gym shortcut is disabled for this deployment.", status=404)
        business_account_public_id = ensure_default_gym_business()
        return redirect(url_for("salonmax_public_gym_site", business_account_public_id=business_account_public_id))

    @app.route("/kado-health")
    def kado_health_check():
        business_account_public_id = ensure_default_gym_business()
        snapshot = salonmax_public_gym_snapshot(business_account_public_id)
        return jsonify(
            {
                "ok": snapshot is not None,
                "business_account_public_id": business_account_public_id,
                "business_name": snapshot["business_name"] if snapshot else "",
                "brand_name": snapshot["brand_name"] if snapshot else "",
            }
        )

    @app.route("/staff")
    def default_gym_staff_shortcut():
        if not gym_product.friendly_shortcuts_enabled():
            return json_error("SHORTCUT_DISABLED", "This gym shortcut is disabled for this deployment.", status=404)
        business_account_public_id = ensure_default_gym_business()
        return redirect(url_for("salonmax_gym_staff_site", business_account_public_id=business_account_public_id))

    @app.route("/check-in")
    @app.route("/checkin")
    def default_gym_reception_shortcut():
        if not gym_product.friendly_shortcuts_enabled():
            return json_error("SHORTCUT_DISABLED", "This gym shortcut is disabled for this deployment.", status=404)
        business_account_public_id = ensure_default_gym_business()
        return redirect(url_for("salonmax_gym_reception_site", business_account_public_id=business_account_public_id))

    @app.route("/gym/<business_account_public_id>")
    @app.route("/gym/<business_account_public_id>/join")
    @app.route("/gym/<business_account_public_id>/customer")
    def salonmax_public_gym_site(business_account_public_id: str):
        return salonmax_gym_surface(business_account_public_id, "customer")

    @app.get("/gym/<business_account_public_id>/state")
    def salonmax_gym_state_get(business_account_public_id: str):
        if business_account_public_id == default_gym_business_public_id():
            ensure_default_gym_business()
        if salonmax_public_gym_snapshot(business_account_public_id) is None:
            return json_error("GYM_NOT_FOUND", "No gym signup site was found for that business account.", status=404)
        return jsonify(
            {
                "ok": True,
                "business_account_public_id": business_account_public_id,
                "state": deps["read_gym_business_state"](business_account_public_id),
                "storage": "postgres" if deps["gym_state_database_url"]() else "sqlite",
            }
        )

    @app.post("/gym/<business_account_public_id>/state")
    def salonmax_gym_state_save(business_account_public_id: str):
        if business_account_public_id == default_gym_business_public_id():
            ensure_default_gym_business()
        if salonmax_public_gym_snapshot(business_account_public_id) is None:
            return json_error("GYM_NOT_FOUND", "No gym signup site was found for that business account.", status=404)
        payload = request.get_json(silent=True) or {}
        state_data = payload.get("state")
        if not isinstance(state_data, dict):
            return json_error("INVALID_STATE", "Gym state must be a JSON object.", status=400)
        if not deps["write_gym_business_state"](business_account_public_id, state_data):
            return json_error("STATE_TOO_LARGE", "Gym state is too large to save safely.", status=413)
        return jsonify({"ok": True, "storage": "postgres" if deps["gym_state_database_url"]() else "sqlite"})

    @app.route("/gym/<business_account_public_id>/reception")
    @app.route("/gym/<business_account_public_id>/check-in")
    @app.route("/gym/<business_account_public_id>/checkin")
    def salonmax_gym_reception_site(business_account_public_id: str):
        if not session.get(gym_staff_session_key(business_account_public_id)):
            return gym_staff_login_redirect(business_account_public_id)
        return salonmax_gym_surface(business_account_public_id, "reception")

    @app.route("/gym/<business_account_public_id>/staff")
    def salonmax_gym_staff_site(business_account_public_id: str):
        if not session.get(gym_staff_session_key(business_account_public_id)):
            return gym_staff_login_redirect(business_account_public_id)
        return salonmax_gym_surface(business_account_public_id, "staff")

    @app.route("/gym/<business_account_public_id>/demo")
    def salonmax_gym_demo_site(business_account_public_id: str):
        if not session.get(gym_staff_session_key(business_account_public_id)):
            return gym_staff_login_redirect(business_account_public_id)
        return salonmax_gym_surface(business_account_public_id, "all")

    @app.route("/gym/<business_account_public_id>/staff-login", methods=["GET", "POST"])
    def salonmax_gym_staff_login(business_account_public_id: str):
        snapshot = salonmax_public_gym_snapshot(business_account_public_id)
        if snapshot is None:
            return json_error("GYM_NOT_FOUND", "No gym signup site was found for that business account.", status=404)

        deps["ensure_gym_staff_auth_table"]()
        next_url = request.values.get("next", url_for("salonmax_gym_staff_site", business_account_public_id=business_account_public_id)).strip()
        if not next_url.startswith("/") or next_url.startswith("//"):
            next_url = url_for("salonmax_gym_staff_site", business_account_public_id=business_account_public_id)

        notice = request.args.get("notice", "").strip()
        auth_row = deps["platform_query_one"](
            "select password_hash from gym_staff_auth where business_account_public_id = ?",
            (business_account_public_id,),
        )

        if request.method == "POST":
            password = request.form.get("password", "")
            if auth_row is None:
                notice = "Staff password is not set yet. Ask Salon Max to set or reset it from the platform."
            elif check_password_hash(auth_row["password_hash"], password):
                session[gym_staff_session_key(business_account_public_id)] = True
                session[f"gym_staff_business_name:{business_account_public_id}"] = snapshot["brand_name"]
                return redirect(next_url)
            else:
                notice = "Login failed. Check the gym staff password."

        return render_template(
            "gym_staff_login.html",
            snapshot=snapshot,
            notice=notice,
            next_url=next_url,
            password_configured=auth_row is not None,
        )

    @app.route("/gym/<business_account_public_id>/staff-logout")
    def salonmax_gym_staff_logout(business_account_public_id: str):
        session.pop(gym_staff_session_key(business_account_public_id), None)
        session.pop(f"gym_staff_business_name:{business_account_public_id}", None)
        return redirect(url_for("salonmax_gym_staff_login", business_account_public_id=business_account_public_id, notice="Signed out."))

    @app.post("/gym/<business_account_public_id>/staff-password")
    def salonmax_gym_staff_change_password(business_account_public_id: str):
        if not session.get(gym_staff_session_key(business_account_public_id)):
            return gym_staff_login_redirect(business_account_public_id)

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        auth_row = deps["platform_query_one"](
            "select password_hash from gym_staff_auth where business_account_public_id = ?",
            (business_account_public_id,),
        )
        if auth_row is None:
            return redirect(url_for("salonmax_gym_staff_site", business_account_public_id=business_account_public_id, notice="Staff password is not set yet. Ask Salon Max to reset it."))
        if not check_password_hash(auth_row["password_hash"], current_password):
            return redirect(url_for("salonmax_gym_staff_site", business_account_public_id=business_account_public_id, notice="Current password was not correct."))
        if len(new_password) < 8:
            return redirect(url_for("salonmax_gym_staff_site", business_account_public_id=business_account_public_id, notice="New staff password must be at least 8 characters."))
        if new_password != confirm_password:
            return redirect(url_for("salonmax_gym_staff_site", business_account_public_id=business_account_public_id, notice="New password and confirmation did not match."))

        deps["platform_execute"](
            """
            update gym_staff_auth
            set password_hash = ?, updated_at = ?
            where business_account_public_id = ?
            """,
            (generate_password_hash(new_password), deps["now_utc_text"](), business_account_public_id),
        )
        return redirect(url_for("salonmax_gym_staff_site", business_account_public_id=business_account_public_id, notice="Staff password changed."))

    @app.post("/gym/<business_account_public_id>/checkout/session")
    def salonmax_gym_create_checkout_session(business_account_public_id: str):
        snapshot = salonmax_public_gym_snapshot(business_account_public_id)
        if snapshot is None:
            return json_error("GYM_NOT_FOUND", "No gym signup site was found for that business account.", status=404)

        payload = request.get_json(silent=True) or {}
        member_id = str(payload.get("member_id") or "").strip()
        member_name = str(payload.get("member_name") or "").strip()
        member_email = str(payload.get("member_email") or "").strip()
        plan_id = str(payload.get("plan_id") or "").strip()
        plan_name = str(payload.get("plan_name") or "").strip()
        billing = str(payload.get("billing") or "one-off").strip()
        try:
            amount = max(0, float(payload.get("amount") or 0))
        except (TypeError, ValueError):
            amount = 0

        if not member_id or not plan_id or not plan_name or amount <= 0:
            return json_error("CHECKOUT_BAD_REQUEST", "Member, package, and amount are required.", status=400)

        settings = deps["gym_payment_settings"](business_account_public_id)
        stripe_secret_key = os.environ.get("SALONMAX_STRIPE_SECRET_KEY", "").strip()
        if not settings["checkout_enabled"] or not settings["provider_account_id"] or not stripe_secret_key:
            return jsonify({
                "ok": True,
                "payment_mode": "setup_required",
                "message": "Real checkout is not enabled yet. Add Stripe secret key and the gym connected account id in Salon Max.",
                "demo_allowed": True,
            })

        base_url = request.host_url.rstrip("/")
        success_url = f"{base_url}{url_for('salonmax_public_gym_site', business_account_public_id=business_account_public_id)}?checkout=success&member_id={member_id}&plan_id={plan_id}&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}{url_for('salonmax_public_gym_site', business_account_public_id=business_account_public_id)}?checkout=cancelled&member_id={member_id}&plan_id={plan_id}"
        unit_amount = int(round(amount * 100))
        application_fee_amount = int(round(unit_amount * float(settings["application_fee_percent"] or 0) / 100))

        params = {
            "mode": "subscription" if billing == "monthly" else "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items[0][price_data][currency]": settings["currency"],
            "line_items[0][price_data][product_data][name]": plan_name,
            "line_items[0][price_data][unit_amount]": str(unit_amount),
            "line_items[0][quantity]": "1",
            "client_reference_id": f"{business_account_public_id}:{member_id}:{plan_id}",
            "metadata[business_account_public_id]": business_account_public_id,
            "metadata[member_id]": member_id,
            "metadata[member_name]": member_name,
            "metadata[plan_id]": plan_id,
            "metadata[plan_name]": plan_name,
        }
        if member_email:
            params["customer_email"] = member_email
        if billing == "monthly":
            params["line_items[0][price_data][recurring][interval]"] = "month"
            if application_fee_amount:
                params["subscription_data[application_fee_percent]"] = str(float(settings["application_fee_percent"]))
        elif application_fee_amount:
            params["payment_intent_data[application_fee_amount]"] = str(application_fee_amount)

        try:
            checkout_session = deps["create_stripe_checkout_session"](
                stripe_secret_key=stripe_secret_key,
                connected_account_id=settings["provider_account_id"],
                params=params,
            )
        except Exception as exc:
            return json_error("STRIPE_CHECKOUT_FAILED", f"Stripe checkout could not be started: {exc}", status=502)

        return jsonify({
            "ok": True,
            "payment_mode": "stripe_checkout",
            "checkout_url": checkout_session.get("url"),
            "checkout_session_id": checkout_session.get("id"),
        })

    @app.get("/gym/<business_account_public_id>/checkout/session/<checkout_session_id>")
    def salonmax_gym_checkout_session_status(business_account_public_id: str, checkout_session_id: str):
        snapshot = salonmax_public_gym_snapshot(business_account_public_id)
        if snapshot is None:
            return json_error("GYM_NOT_FOUND", "No gym signup site was found for that business account.", status=404)

        deps["ensure_gym_checkout_events_table"]()
        event_row = deps["platform_query_one"](
            """
            select *
            from gym_checkout_events
            where business_account_public_id = ?
              and checkout_session_id = ?
            """,
            (business_account_public_id, checkout_session_id),
        )
        if event_row is not None and str(event_row["payment_status"]).lower() == "paid":
            return jsonify({
                "ok": True,
                "confirmed": True,
                "source": "webhook",
                "member_id": event_row["member_id"],
                "member_name": event_row["member_name"],
                "plan_id": event_row["plan_id"],
                "plan_name": event_row["plan_name"],
                "payment_status": event_row["payment_status"],
            })

        settings = deps["gym_payment_settings"](business_account_public_id)
        stripe_secret_key = os.environ.get("SALONMAX_STRIPE_SECRET_KEY", "").strip()
        if not stripe_secret_key or not settings["provider_account_id"]:
            return jsonify({"ok": True, "confirmed": False, "message": "Stripe is not configured yet."})

        try:
            checkout_session = deps["retrieve_stripe_checkout_session"](
                stripe_secret_key=stripe_secret_key,
                connected_account_id=settings["provider_account_id"],
                checkout_session_id=checkout_session_id,
            )
        except Exception as exc:
            return json_error("STRIPE_SESSION_LOOKUP_FAILED", f"Stripe checkout session could not be checked: {exc}", status=502)

        metadata = checkout_session.get("metadata") or {}
        if metadata.get("business_account_public_id") != business_account_public_id:
            return json_error("CHECKOUT_BUSINESS_MISMATCH", "Stripe session does not belong to this gym.", status=403)

        if checkout_session.get("payment_status") == "paid":
            deps["save_gym_checkout_event_from_session"]("checkout.session.confirmed", checkout_session)
            return jsonify({
                "ok": True,
                "confirmed": True,
                "source": "stripe_lookup",
                "member_id": metadata.get("member_id"),
                "member_name": metadata.get("member_name"),
                "plan_id": metadata.get("plan_id"),
                "plan_name": metadata.get("plan_name"),
                "payment_status": checkout_session.get("payment_status"),
            })

        return jsonify({
            "ok": True,
            "confirmed": False,
            "source": "stripe_lookup",
            "payment_status": checkout_session.get("payment_status"),
            "checkout_status": checkout_session.get("status"),
        })

    @app.post("/stripe/webhook")
    def salonmax_stripe_webhook():
        payload = request.get_data(cache=False)
        signature_header = request.headers.get("Stripe-Signature", "")
        webhook_secret = os.environ.get("SALONMAX_STRIPE_WEBHOOK_SECRET", "").strip()
        if not webhook_secret:
            return json_error("WEBHOOK_SECRET_MISSING", "Stripe webhook secret is not configured.", status=500)
        if not deps["verify_stripe_signature"](payload, signature_header, webhook_secret):
            return json_error("WEBHOOK_SIGNATURE_INVALID", "Stripe webhook signature was invalid.", status=400)

        try:
            event = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            return json_error("WEBHOOK_BAD_JSON", "Stripe webhook body was not valid JSON.", status=400)

        event_type = event.get("type", "")
        data_object = ((event.get("data") or {}).get("object") or {})
        if event_type == "checkout.session.completed":
            deps["save_gym_checkout_event_from_session"](event.get("id", ""), data_object, raw_event=event)
        return jsonify({"ok": True, "received": True})
