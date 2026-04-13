from __future__ import annotations

import argparse
import secrets
from datetime import date, datetime

from sqlalchemy import text

from database.config import engine


PATIENT_PREFIX = "PID"
PATIENT_RANDOM_WIDTH = 3
PATIENT_MAX_ATTEMPTS = 1500
STAFF_RANDOM_WIDTH = 4
STAFF_MAX_ATTEMPTS = 2000
STAFF_ROLE_PREFIXES = {
    "admin": "ADM",
    "doctor": "DOC",
    "nurse": "NUR",
    "record_officer": "REC",
    "pharmacist": "PHA",
    "lab_scientist": "LAB",
}


def _resolve_date(value: str | None = None) -> date:
    if not value:
        return datetime.now().date()
    return date.fromisoformat(value)


def _normalize_role(role: str) -> str:
    normalized_role = role.strip().lower()
    if normalized_role not in STAFF_ROLE_PREFIXES:
        supported_roles = ", ".join(sorted(STAFF_ROLE_PREFIXES))
        raise ValueError(f"Unsupported role '{role}'. Expected one of: {supported_roles}.")
    return normalized_role


def _random_digits(width: int) -> str:
    upper_limit = (10**width) - 1
    return f"{secrets.randbelow(upper_limit) + 1:0{width}d}"


def _patient_day_code(registration_date: date) -> str:
    return registration_date.strftime("%A")[0].upper()


def _patient_month_code(registration_date: date) -> str:
    return registration_date.strftime("%b").upper()


def _format_pid(registration_date: date, random_digits: str) -> str:
    day_code = _patient_day_code(registration_date)
    month_code = _patient_month_code(registration_date)
    return f"{PATIENT_PREFIX}-{day_code}{random_digits}-{month_code}"


def _format_staff_id(role: str, random_digits: str) -> str:
    role_prefix = STAFF_ROLE_PREFIXES[role]
    return f"{role_prefix}-{random_digits}"


def _patient_id_exists(conn, pid: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM patients
                    WHERE pid = :pid
                );
                """
            ),
            {"pid": pid},
        ).scalar()
    )


def _staff_id_exists(conn, staff_id: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM users
                    WHERE staff_id = :staff_id
                );
                """
            ),
            {"staff_id": staff_id},
        ).scalar()
    )


def _generate_patient_id_for_connection(conn, resolved_date: date) -> str:
    for _ in range(PATIENT_MAX_ATTEMPTS):
        candidate = _format_pid(resolved_date, _random_digits(PATIENT_RANDOM_WIDTH))
        if not _patient_id_exists(conn, candidate):
            return candidate

    raise RuntimeError(
        f"Unable to generate a unique patient ID for {resolved_date.isoformat()} "
        f"after {PATIENT_MAX_ATTEMPTS} attempts."
    )


def _generate_staff_id_for_connection(conn, normalized_role: str) -> str:
    for _ in range(STAFF_MAX_ATTEMPTS):
        candidate = _format_staff_id(normalized_role, _random_digits(STAFF_RANDOM_WIDTH))
        if not _staff_id_exists(conn, candidate):
            return candidate

    raise RuntimeError(
        f"Unable to generate a unique staff ID for role '{normalized_role}' "
        f"after {STAFF_MAX_ATTEMPTS} attempts."
    )


def generate_patient_id(registration_date: str | None = None, conn=None) -> str:
    resolved_date = _resolve_date(registration_date)

    if conn is not None:
        return _generate_patient_id_for_connection(conn, resolved_date)

    with engine.connect() as connection:
        return _generate_patient_id_for_connection(connection, resolved_date)


def generate_staff_id(role: str, conn=None) -> str:
    normalized_role = _normalize_role(role)

    if conn is not None:
        return _generate_staff_id_for_connection(conn, normalized_role)

    with engine.connect() as connection:
        return _generate_staff_id_for_connection(connection, normalized_role)


def preview_patient_id(registration_date: str | None = None, conn=None) -> str:
    return generate_patient_id(registration_date, conn=conn)


def preview_staff_id(role: str, conn=None) -> str:
    return generate_staff_id(role, conn=conn)


def reserve_patient_id(registration_date: str | None = None, conn=None) -> str:
    return generate_patient_id(registration_date, conn=conn)


def reserve_staff_id(role: str, conn=None) -> str:
    return generate_staff_id(role, conn=conn)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate patient and staff identifiers."
    )
    parser.add_argument(
        "action",
        choices=["preview", "reserve"],
        help="Generate an ID. Use reserve when you intend to insert immediately after generation.",
    )
    parser.add_argument(
        "entity",
        choices=["patient", "staff"],
        help="Which identifier type to generate.",
    )
    parser.add_argument(
        "--role",
        choices=sorted(STAFF_ROLE_PREFIXES),
        help="Required when generating a staff ID.",
    )
    parser.add_argument(
        "--date",
        help="Patient registration date in YYYY-MM-DD format. Defaults to today.",
    )
    args = parser.parse_args()

    if args.entity == "staff" and not args.role:
        parser.error("--role is required when entity is 'staff'.")

    if args.entity == "patient":
        print(generate_patient_id(args.date))
        return

    print(generate_staff_id(args.role))


if __name__ == "__main__":
    main()
