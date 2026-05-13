from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from zoneinfo import ZoneInfo


def default_business_public_id() -> str:
    return (
        os.environ.get("SALONMAX_DEFAULT_GYM_BUSINESS_ID", "").strip()
        or os.environ.get("KADO_GYM_BUSINESS_ID", "").strip()
        or "biz_test-2"
    )


def default_business_name() -> str:
    return os.environ.get("SALONMAX_DEFAULT_GYM_BUSINESS_NAME", "KADO Fitness").strip() or "KADO Fitness"


def default_staff_password() -> str:
    return os.environ.get("SALONMAX_DEFAULT_GYM_STAFF_PASSWORD", "KadoStaff2026").strip() or "KadoStaff2026"


def friendly_shortcuts_enabled() -> bool:
    return os.environ.get("SALONMAX_GYM_FRIENDLY_SHORTCUTS", "1").strip() != "0"


def cloud_home_target() -> str:
    return os.environ.get("SALONMAX_CLOUD_HOME", "default_gym").strip().lower() or "default_gym"


def fallback_brand_name(business_account_public_id: str) -> str:
    if business_account_public_id == default_business_public_id():
        return default_business_name()
    return "Gym"


def staff_session_key(business_account_public_id: str) -> str:
    return f"gym_staff_authenticated:{business_account_public_id}"


def ensure_staff_auth_table(platform_execute):
    platform_execute(
        """
        create table if not exists gym_staff_auth (
            id integer primary key autoincrement,
            business_account_public_id text not null unique,
            password_hash text not null,
            updated_at text not null
        )
        """
    )


def ensure_payment_settings_table(platform_execute):
    platform_execute(
        """
        create table if not exists gym_payment_settings (
            id integer primary key autoincrement,
            business_account_public_id text not null unique,
            provider text not null default 'stripe_connect',
            provider_account_id text not null default '',
            currency text not null default 'gbp',
            application_fee_percent real not null default 0,
            checkout_enabled integer not null default 0,
            updated_at text not null
        )
        """
    )


def ensure_checkout_events_table(platform_execute):
    platform_execute(
        """
        create table if not exists gym_checkout_events (
            id integer primary key autoincrement,
            stripe_event_id text unique,
            checkout_session_id text unique,
            business_account_public_id text not null,
            member_id text not null,
            member_name text not null default '',
            plan_id text not null,
            plan_name text not null default '',
            amount_total integer not null default 0,
            currency text not null default 'gbp',
            payment_status text not null default '',
            checkout_status text not null default '',
            event_type text not null default '',
            raw_json text not null default '',
            created_at text not null,
            updated_at text not null
        )
        """
    )


def state_database_url() -> str:
    return os.environ.get("SALONMAX_DATABASE_URL", "").strip() or os.environ.get("DATABASE_URL", "").strip()


def state_pg_connect():
    database_url = state_database_url()
    if not database_url:
        return None
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        return None
    return psycopg.connect(database_url, row_factory=dict_row)


def ensure_state_table(platform_execute):
    pg_connection = state_pg_connect()
    if pg_connection is not None:
        with pg_connection:
            pg_connection.execute(
                """
                create table if not exists gym_business_state (
                    business_account_public_id text primary key,
                    state_json jsonb not null,
                    updated_at timestamptz not null default now()
                )
                """
            )
        return

    platform_execute(
        """
        create table if not exists gym_business_state (
            business_account_public_id text primary key,
            state_json text not null,
            updated_at text not null
        )
        """
    )


def read_business_state(business_account_public_id: str, platform_execute, platform_query_one):
    ensure_state_table(platform_execute)
    pg_connection = state_pg_connect()
    if pg_connection is not None:
        with pg_connection:
            row = pg_connection.execute(
                """
                select state_json
                from gym_business_state
                where business_account_public_id = %s
                """,
                (business_account_public_id,),
            ).fetchone()
        if row is None:
            return None
        return row["state_json"]

    row = platform_query_one(
        """
        select state_json
        from gym_business_state
        where business_account_public_id = ?
        """,
        (business_account_public_id,),
    )
    if row is None:
        return None
    try:
        return json.loads(row["state_json"])
    except json.JSONDecodeError:
        return None


def write_business_state(business_account_public_id: str, state_data: dict, platform_execute, now_utc_text) -> bool:
    ensure_state_table(platform_execute)
    state_json = json.dumps(state_data, separators=(",", ":"), sort_keys=True)
    if len(state_json) > 2_000_000:
        return False

    pg_connection = state_pg_connect()
    if pg_connection is not None:
        with pg_connection:
            pg_connection.execute(
                """
                insert into gym_business_state (business_account_public_id, state_json, updated_at)
                values (%s, %s::jsonb, now())
                on conflict (business_account_public_id)
                do update set state_json = excluded.state_json, updated_at = now()
                """,
                (business_account_public_id, state_json),
            )
        return True

    platform_execute(
        """
        insert into gym_business_state (business_account_public_id, state_json, updated_at)
        values (?, ?, ?)
        on conflict(business_account_public_id)
        do update set state_json = excluded.state_json, updated_at = excluded.updated_at
        """,
        (business_account_public_id, state_json, now_utc_text()),
    )
    return True


def ensure_default_business(
    *,
    ensure_platform_sync_tables,
    platform_execute,
    platform_query_one,
    generate_password_hash,
    now_utc_text,
) -> str:
    business_account_public_id = default_business_public_id()
    business_name = default_business_name()
    ensure_platform_sync_tables()
    existing = platform_query_one(
        "select id from cloud_business_accounts where business_account_public_id = ?",
        (business_account_public_id,),
    )
    if existing is None:
        platform_execute(
            """
            insert into cloud_business_accounts (
                business_account_public_id,
                business_name,
                product_type,
                status,
                subscription_plan,
                subscription_status,
                contact_name,
                contact_email,
                contact_phone,
                city,
                postcode,
                monthly_fee,
                notes
            ) values (?, ?, 'gym', 'active', 'gym_access', 'trial', '', '', '', '', '', '100', ?)
            """,
            (
                business_account_public_id,
                business_name,
                f"Auto-created default gym business for {business_name} while the production database is being prepared.",
            ),
        )

    ensure_staff_auth_table(platform_execute)
    auth = platform_query_one(
        "select id from gym_staff_auth where business_account_public_id = ?",
        (business_account_public_id,),
    )
    if auth is None:
        platform_execute(
            """
            insert into gym_staff_auth (business_account_public_id, password_hash, updated_at)
            values (?, ?, ?)
            """,
            (business_account_public_id, generate_password_hash(default_staff_password()), now_utc_text()),
        )
    return business_account_public_id


def payment_settings(business_account_public_id: str, platform_execute, platform_query_one):
    ensure_payment_settings_table(platform_execute)
    row = platform_query_one(
        "select * from gym_payment_settings where business_account_public_id = ?",
        (business_account_public_id,),
    )
    return {
        "provider": row["provider"] if row else "stripe_connect",
        "provider_account_id": row["provider_account_id"] if row else "",
        "currency": row["currency"] if row else "gbp",
        "application_fee_percent": float(row["application_fee_percent"] if row else 0),
        "checkout_enabled": bool(row["checkout_enabled"] if row else 0),
    }


def verify_stripe_signature(payload: bytes, signature_header: str, webhook_secret: str, tolerance_seconds: int = 300) -> bool:
    parts = {}
    for item in signature_header.split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            parts.setdefault(key, []).append(value)
    try:
        timestamp = int((parts.get("t") or [""])[0])
    except ValueError:
        return False
    if abs(datetime.now(ZoneInfo("UTC")).timestamp() - timestamp) > tolerance_seconds:
        return False
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    expected = hmac.new(webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, signature) for signature in parts.get("v1", []))


def save_checkout_event_from_session(
    event_id: str,
    checkout_session: dict,
    *,
    platform_execute,
    platform_query_one,
    now_utc_text,
    raw_event: dict | None = None,
):
    ensure_checkout_events_table(platform_execute)
    metadata = checkout_session.get("metadata") or {}
    business_account_public_id = str(metadata.get("business_account_public_id") or "").strip()
    member_id = str(metadata.get("member_id") or "").strip()
    plan_id = str(metadata.get("plan_id") or "").strip()
    checkout_session_id = str(checkout_session.get("id") or "").strip()
    if not business_account_public_id or not member_id or not plan_id or not checkout_session_id:
        return

    existing = platform_query_one(
        "select id from gym_checkout_events where checkout_session_id = ?",
        (checkout_session_id,),
    )
    values = (
        event_id or checkout_session_id,
        checkout_session_id,
        business_account_public_id,
        member_id,
        str(metadata.get("member_name") or ""),
        plan_id,
        str(metadata.get("plan_name") or ""),
        int(checkout_session.get("amount_total") or 0),
        str(checkout_session.get("currency") or "gbp"),
        str(checkout_session.get("payment_status") or ""),
        str(checkout_session.get("status") or ""),
        "checkout.session.completed",
        json.dumps(raw_event or checkout_session),
        now_utc_text(),
        now_utc_text(),
    )
    if existing is None:
        platform_execute(
            """
            insert into gym_checkout_events (
                stripe_event_id,
                checkout_session_id,
                business_account_public_id,
                member_id,
                member_name,
                plan_id,
                plan_name,
                amount_total,
                currency,
                payment_status,
                checkout_status,
                event_type,
                raw_json,
                created_at,
                updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    else:
        platform_execute(
            """
            update gym_checkout_events
            set stripe_event_id = ?,
                business_account_public_id = ?,
                member_id = ?,
                member_name = ?,
                plan_id = ?,
                plan_name = ?,
                amount_total = ?,
                currency = ?,
                payment_status = ?,
                checkout_status = ?,
                event_type = ?,
                raw_json = ?,
                updated_at = ?
            where checkout_session_id = ?
            """,
            (
                values[0], values[2], values[3], values[4], values[5], values[6],
                values[7], values[8], values[9], values[10], values[11], values[12],
                values[14], values[1],
            ),
        )


def create_stripe_checkout_session(stripe_secret_key: str, connected_account_id: str, params: dict):
    encoded = urlencode(params).encode("utf-8")
    request_obj = UrlRequest(
        "https://api.stripe.com/v1/checkout/sessions",
        data=encoded,
        headers={
            "Authorization": f"Bearer {stripe_secret_key}",
            "Stripe-Account": connected_account_id,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urlopen(request_obj, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def retrieve_stripe_checkout_session(stripe_secret_key: str, connected_account_id: str, checkout_session_id: str):
    request_obj = UrlRequest(
        f"https://api.stripe.com/v1/checkout/sessions/{checkout_session_id}",
        headers={
            "Authorization": f"Bearer {stripe_secret_key}",
            "Stripe-Account": connected_account_id,
        },
        method="GET",
    )
    with urlopen(request_obj, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))
