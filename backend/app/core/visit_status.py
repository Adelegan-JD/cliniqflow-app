"""Canonical visit_status strings for API responses (aligned with product visit_service)."""

WAITING_FOR_TRIAGE = "WAITING_FOR_TRIAGE"
WAITING_FOR_DOCTOR = "WAITING_FOR_DOCTOR"
WITH_DOCTOR = "WITH_DOCTOR"
COMPLETED = "COMPLETED"
CANCELLED = "CANCELLED"

# Legacy values still accepted when normalizing old in-memory rows
_LEGACY = {
    "TRIAGED": WAITING_FOR_DOCTOR,
    "WAITING_FOR_CONSULTATION": WAITING_FOR_DOCTOR,
    "IN_CONSULTATION": WITH_DOCTOR,
}


def normalize_visit_status(raw: str | None) -> str:
    if not raw:
        return WAITING_FOR_TRIAGE
    if raw in (
        WAITING_FOR_TRIAGE,
        WAITING_FOR_DOCTOR,
        WITH_DOCTOR,
        COMPLETED,
        CANCELLED,
    ):
        return raw
    return _LEGACY.get(raw, raw)
