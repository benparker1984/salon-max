from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_headers = dict(headers or {})
    request_bytes = None
    if body is not None:
        request_headers["Content-Type"] = "application/json"
        request_bytes = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    request = Request(url, data=request_bytes, headers=request_headers, method=method.upper())
    try:
        with urlopen(request, timeout=20) as response:
            response_text = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(response_text or "{}")
        except json.JSONDecodeError:
            payload = {"ok": False, "error": {"code": "HTTP_ERROR", "message": response_text}}
        raise RuntimeError(json.dumps(payload, indent=2))
    except (URLError, OSError) as exc:
        raise RuntimeError(str(exc)) from exc

    try:
        return json.loads(response_text or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from {url}") from exc


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def command_pair(args) -> int:
    response = request_json(
        "POST",
        f"{args.base_url.rstrip('/')}/v1/devices/pair",
        body={
            "pairing_code": args.pairing_code.strip().upper(),
            "device_serial": args.device_serial.strip() or args.state_file.stem,
            "terminal_name": args.terminal_name.strip() or "Simulated Till",
        },
    )
    data = response.get("data") if isinstance(response, dict) else None
    if not isinstance(data, dict):
        print(json.dumps(response, indent=2))
        return 1
    state = {
        "base_url": args.base_url.rstrip("/"),
        "business_account_public_id": str(data.get("business_account_public_id") or ""),
        "site_public_id": str(data.get("site_public_id") or ""),
        "terminal_device_public_id": str(data.get("terminal_device_public_id") or ""),
        "terminal_name": str(data.get("terminal_name") or ""),
        "signed_token": str(data.get("signed_token") or ""),
        "expires_at": str(data.get("expires_at") or ""),
        "issued_at": str(data.get("issued_at") or ""),
        "device_serial": args.device_serial.strip() or args.state_file.stem,
    }
    save_state(args.state_file, state)
    print(json.dumps(state, indent=2))
    return 0


def command_check_in(args) -> int:
    state = load_state(args.state_file)
    if not state:
        print("State file is missing or empty. Pair the terminal first.")
        return 1
    response = request_json(
        "POST",
        f"{state['base_url']}/v1/licence/check-in",
        headers={
            "Authorization": f"Bearer {state['signed_token']}",
            "X-SalonMax-Business-Id": state["business_account_public_id"],
            "X-SalonMax-Device-Id": state["terminal_device_public_id"],
        },
        body={
            "terminal_device_id": state["terminal_device_public_id"],
            "app_version": args.app_version,
            "sync_health": {
                "status": args.sync_status,
                "pending_count": args.pending_count,
                "failed_count": args.failed_count,
                "recent_failed_items": [],
                "recent_pending_items": [],
            },
        },
    )
    data = response.get("data") if isinstance(response, dict) else None
    if isinstance(data, dict):
        state["signed_token"] = str(data.get("signed_token") or state.get("signed_token") or "")
        state["expires_at"] = str(data.get("expires_at") or state.get("expires_at") or "")
        save_state(args.state_file, state)
    print(json.dumps(response, indent=2))
    return 0


def command_config(args) -> int:
    state = load_state(args.state_file)
    if not state:
        print("State file is missing or empty. Pair the terminal first.")
        return 1
    response = request_json(
        "GET",
        f"{state['base_url']}/v1/devices/{quote(state['terminal_device_public_id'], safe='')}/config",
        headers={
            "Authorization": f"Bearer {state['signed_token']}",
            "X-SalonMax-Device-Id": state["terminal_device_public_id"],
        },
    )
    print(json.dumps(response, indent=2))
    return 0


def command_customers(args) -> int:
    state = load_state(args.state_file)
    if not state:
        print("State file is missing or empty. Pair the terminal first.")
        return 1
    request_url = f"{state['base_url']}/v1/customers/directory"
    if args.updated_since:
        request_url += f"?updated_since={quote(args.updated_since, safe='')}"
    response = request_json(
        "GET",
        request_url,
        headers={
            "Authorization": f"Bearer {state['signed_token']}",
            "X-SalonMax-Business-Id": state["business_account_public_id"],
            "X-SalonMax-Device-Id": state["terminal_device_public_id"],
        },
    )
    print(json.dumps(response, indent=2))
    return 0


def command_corrections(args) -> int:
    state = load_state(args.state_file)
    if not state:
        print("State file is missing or empty. Pair the terminal first.")
        return 1
    request_url = (
        f"{state['base_url']}/v1/customers/corrections"
        f"?since_minute_ledger_id={max(0, int(args.since_minute_ledger_id))}"
        f"&since_balance_ledger_id={max(0, int(args.since_balance_ledger_id))}"
    )
    response = request_json(
        "GET",
        request_url,
        headers={
            "Authorization": f"Bearer {state['signed_token']}",
            "X-SalonMax-Business-Id": state["business_account_public_id"],
            "X-SalonMax-Device-Id": state["terminal_device_public_id"],
        },
    )
    print(json.dumps(response, indent=2))
    return 0


def command_state(args) -> int:
    state = load_state(args.state_file)
    print(json.dumps(state, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate a Salon Max terminal against the cloud APIs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pair_parser = subparsers.add_parser("pair", help="Pair a simulated terminal with a pairing code.")
    pair_parser.add_argument("--base-url", required=True, help="Base URL, e.g. http://100.71.173.23:5001")
    pair_parser.add_argument("--pairing-code", required=True)
    pair_parser.add_argument("--terminal-name", default="Simulated Till")
    pair_parser.add_argument("--device-serial", default="")
    pair_parser.add_argument("--state-file", required=True, type=Path)
    pair_parser.set_defaults(func=command_pair)

    check_in_parser = subparsers.add_parser("check-in", help="Perform a licence check-in.")
    check_in_parser.add_argument("--state-file", required=True, type=Path)
    check_in_parser.add_argument("--app-version", default="sim-terminal-dev")
    check_in_parser.add_argument("--sync-status", default="healthy")
    check_in_parser.add_argument("--pending-count", type=int, default=0)
    check_in_parser.add_argument("--failed-count", type=int, default=0)
    check_in_parser.set_defaults(func=command_check_in)

    config_parser = subparsers.add_parser("config", help="Fetch device config.")
    config_parser.add_argument("--state-file", required=True, type=Path)
    config_parser.set_defaults(func=command_config)

    customers_parser = subparsers.add_parser("customers", help="Fetch customer directory feed.")
    customers_parser.add_argument("--state-file", required=True, type=Path)
    customers_parser.add_argument("--updated-since", default="")
    customers_parser.set_defaults(func=command_customers)

    corrections_parser = subparsers.add_parser("corrections", help="Fetch customer correction feed.")
    corrections_parser.add_argument("--state-file", required=True, type=Path)
    corrections_parser.add_argument("--since-minute-ledger-id", type=int, default=0)
    corrections_parser.add_argument("--since-balance-ledger-id", type=int, default=0)
    corrections_parser.set_defaults(func=command_corrections)

    state_parser = subparsers.add_parser("state", help="Show saved state.")
    state_parser.add_argument("--state-file", required=True, type=Path)
    state_parser.set_defaults(func=command_state)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except RuntimeError as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
