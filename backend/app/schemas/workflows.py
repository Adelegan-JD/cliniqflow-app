from pydantic import BaseModel, Field


class RegisterPatientBody(BaseModel):
    firstName: str
    lastName: str
    otherNames: str | None = None
    dob: str
    gender: str
    civilStatus: str | None = None
    religion: str | None = None
    tribe: str | None = None
    nationality: str | None = None
    phone: str
    altPhone: str | None = None
    email: str | None = None
    address: str
    state: str | None = None
    lga: str | None = None
    nin: str | None = None
    nhisNumber: str | None = None
    militaryNumber: str | None = None
    education: str | None = None
    occupation: str | None = None
    nokName: str
    nokRelationship: str
    nokPhone: str
    nokAddress: str | None = None


class CreateVisitBody(BaseModel):
    patient_id: str
    reason_for_visit: str | None = None
    department: str | None = None
