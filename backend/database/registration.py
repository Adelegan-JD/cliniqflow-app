from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from auth.security import resolve_password_hash
from database.config import engine
from database.id_generator import _normalize_role, reserve_patient_id, reserve_staff_id


ID_COLLISION_RETRIES = 10
PATIENT_METADATA_FIELDS = (
    "email",
    "phone",
    "other_phone_number",
    "address",
    "state_of_origin",
    "lga",
    "nationality",
    "tribe",
    "religion",
    "education",
    "civil_status",
    "nin",
    "nhis_number",
    "military_service_number",
    "next_of_kin_name",
    "next_of_kin_relationship",
    "next_of_kin_phone",
    "next_of_kin_address",
)


def _normalize_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _calculate_age(date_of_birth: date, on_date: date | None = None) -> int:
    reference_date = on_date or datetime.now().date()
    return reference_date.year - date_of_birth.year - (
        (reference_date.month, reference_date.day)
        < (date_of_birth.month, date_of_birth.day)
    )


def _mapping_row(result):
    return dict(result.mappings().one())


def _constraint_name(error: IntegrityError) -> str | None:
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def _is_unique_violation(error: IntegrityError, constraint_name: str) -> bool:
    return getattr(error.orig, "pgcode", None) == "23505" and _constraint_name(error) == constraint_name


def _is_foreign_key_violation(error: IntegrityError, constraint_name: str) -> bool:
    return getattr(error.orig, "pgcode", None) == "23503" and _constraint_name(error) == constraint_name


def _has_metadata_values(metadata: dict | None) -> bool:
    if not metadata:
        return False
    return any(value not in (None, "") for value in metadata.values())


def _build_patient_metadata_params(pid: str, metadata: dict) -> dict:
    params = {field: metadata.get(field) for field in PATIENT_METADATA_FIELDS}
    params["patient_id"] = pid
    return params


def _insert_staff(conn, *, staff_id: str, staff_data: dict) -> dict:
    result = conn.execute(
        text(
            """
            INSERT INTO users (
                staff_id,
                first_name,
                last_name,
                other_names,
                email,
                phone,
                password_hash,
                role,
                department,
                license_number,
                status
            )
            VALUES (
                :staff_id,
                :first_name,
                :last_name,
                :other_names,
                :email,
                :phone,
                :password_hash,
                :role,
                :department,
                :license_number,
                :status
            )
            RETURNING
                id,
                staff_id,
                first_name,
                last_name,
                other_names,
                email,
                phone,
                role,
                department,
                license_number,
                status,
                created_at,
                updated_at;
            """
        ),
        {
            "staff_id": staff_id,
            "first_name": staff_data["first_name"],
            "last_name": staff_data["last_name"],
            "other_names": staff_data.get("other_names"),
            "email": staff_data["email"],
            "phone": staff_data.get("phone"),
            "password_hash": staff_data["password_hash"],
            "role": staff_data["role"],
            "department": staff_data.get("department"),
            "license_number": staff_data.get("license_number"),
            "status": staff_data.get("status", "Offline"),
        },
    )
    return _mapping_row(result)


def _insert_patient(conn, *, pid: str, patient_data: dict) -> dict:
    date_of_birth = _normalize_date(patient_data["date_of_birth"])
    registration_date = _normalize_date(
        patient_data.get("registration_date", datetime.now().date())
    )
    age = patient_data.get("age")
    if age is None:
        age = _calculate_age(date_of_birth, registration_date)

    patient_result = conn.execute(
        text(
            """
            INSERT INTO patients (
                pid,
                first_name,
                last_name,
                other_names,
                date_of_birth,
                gender,
                age,
                passport_url,
                registered_by
            )
            VALUES (
                :pid,
                :first_name,
                :last_name,
                :other_names,
                :date_of_birth,
                :gender,
                :age,
                :passport_url,
                :registered_by
            )
            RETURNING
                id,
                pid,
                first_name,
                last_name,
                other_names,
                date_of_birth,
                gender,
                age,
                passport_url,
                registered_by,
                created_at,
                updated_at;
            """
        ),
        {
            "pid": pid,
            "first_name": patient_data["first_name"],
            "last_name": patient_data["last_name"],
            "other_names": patient_data.get("other_names"),
            "date_of_birth": date_of_birth,
            "gender": patient_data["gender"],
            "age": age,
            "passport_url": patient_data.get("passport_url"),
            "registered_by": patient_data.get("registered_by"),
        },
    )
    patient = _mapping_row(patient_result)

    metadata = None
    if _has_metadata_values(patient_data.get("metadata")):
        metadata_result = conn.execute(
            text(
                """
                INSERT INTO patients_metadata (
                    patient_id,
                    email,
                    phone,
                    other_phone_number,
                    address,
                    state_of_origin,
                    lga,
                    nationality,
                    tribe,
                    religion,
                    education,
                    civil_status,
                    nin,
                    nhis_number,
                    military_service_number,
                    next_of_kin_name,
                    next_of_kin_relationship,
                    next_of_kin_phone,
                    next_of_kin_address
                )
                VALUES (
                    :patient_id,
                    :email,
                    :phone,
                    :other_phone_number,
                    :address,
                    :state_of_origin,
                    :lga,
                    :nationality,
                    :tribe,
                    :religion,
                    :education,
                    :civil_status,
                    :nin,
                    :nhis_number,
                    :military_service_number,
                    :next_of_kin_name,
                    :next_of_kin_relationship,
                    :next_of_kin_phone,
                    :next_of_kin_address
                )
                RETURNING
                    id,
                    patient_id,
                    email,
                    phone,
                    other_phone_number,
                    address,
                    state_of_origin,
                    lga,
                    nationality,
                    tribe,
                    religion,
                    education,
                    civil_status,
                    nin,
                    nhis_number,
                    military_service_number,
                    next_of_kin_name,
                    next_of_kin_relationship,
                    next_of_kin_phone,
                    next_of_kin_address,
                    created_at,
                    updated_at;
                """
            ),
            _build_patient_metadata_params(pid, patient_data["metadata"]),
        )
        metadata = _mapping_row(metadata_result)

    return {"patient": patient, "metadata": metadata}


def register_staff(*, conn=None, **staff_data) -> dict:
    normalized_staff_data = dict(staff_data)
    normalized_staff_data["role"] = _normalize_role(normalized_staff_data["role"])
    normalized_staff_data["password_hash"] = resolve_password_hash(
        password=normalized_staff_data.pop("password", None),
        password_hash=normalized_staff_data.get("password_hash"),
    )

    if conn is not None:
        staff_id = reserve_staff_id(normalized_staff_data["role"], conn=conn)
        return _insert_staff(conn, staff_id=staff_id, staff_data=normalized_staff_data)

    for _ in range(ID_COLLISION_RETRIES):
        try:
            with engine.begin() as connection:
                staff_id = reserve_staff_id(normalized_staff_data["role"], conn=connection)
                return _insert_staff(connection, staff_id=staff_id, staff_data=normalized_staff_data)
        except IntegrityError as error:
            if _is_unique_violation(error, "users_staff_id_key"):
                continue
            if _is_unique_violation(error, "users_email_key"):
                raise ValueError("A staff account with this email already exists.") from error
            raise

    raise RuntimeError("Unable to register staff after repeated staff_id collisions.")


def register_patient(*, conn=None, **patient_data) -> dict:
    if conn is not None:
        pid = reserve_patient_id(patient_data.get("registration_date"), conn=conn)
        return _insert_patient(conn, pid=pid, patient_data=patient_data)

    for _ in range(ID_COLLISION_RETRIES):
        try:
            with engine.begin() as connection:
                pid = reserve_patient_id(patient_data.get("registration_date"), conn=connection)
                return _insert_patient(connection, pid=pid, patient_data=patient_data)
        except IntegrityError as error:
            if _is_unique_violation(error, "patients_pid_key"):
                continue
            if _is_foreign_key_violation(error, "patients_registered_by_fkey"):
                raise ValueError("registered_by must reference an existing staff_id.") from error
            if _is_unique_violation(error, "patients_metadata_patient_id_key"):
                raise ValueError("Patient metadata already exists for this patient.") from error
            raise

    raise RuntimeError("Unable to register patient after repeated pid collisions.")
