from __future__ import annotations

import os


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
