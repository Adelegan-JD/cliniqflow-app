# CliniqFlow Patient Data Flow Analysis

## 1. MOCK/DUMMY PATIENT DATA

### Frontend Mock Data

#### [ActivePatientsList.jsx](frontend/src/components/ActivePatientsList.jsx)

- **Type**: Hardcoded patient array export
- **Mock Data**: 7 patients with complete vitals
- **Fields**: id, name, Age, urgency, active status, status, vitals (temperature, BP, heart rate, respiratory rate, weight, height, BMI)
- **Usage**: Component testing/demo purposes
- **Status**: NOT USED in current implementation (data is fetched from API)

```javascript
export const patientsList = [
  { id: 1, name: "Aisha Bello", Age: 28, urgency: "Emergency", active: true, status: "Triaged", vitals: {...} },
  // ... 6 more patients
]
```

#### [PatientsQueue.jsx](frontend/src/pages/Doctor/PatientsQueue.jsx) (Lines 5-46)

- **Type**: Hardcoded queue patient array
- **Mock Data**: 6 patients with queue status
- **Fields**: patientId, sessionId, name, age, sex, status (awaiting_consultation, awaiting_triage, visit_ended)
- **Usage**: Doctor's patient queue display
- **Status**: HARDCODED - should be replaced with API data

```javascript
const queuePatients = [
  {
    patientId: "PT-001-AB",
    sessionId: "VS-2026-0001",
    name: "Amina Bello",
    age: 34,
    sex: "Female",
    status: "awaiting_consultation",
  },
  // ... 5 more patients
];
```

#### [ActiveQueue.jsx](frontend/src/components/ActiveQueue.jsx) (Lines 31-48)

- **Type**: Commented-out mock data
- **Note**: Old mock data present in comments, currently not active

---

## 2. COMPONENTS THAT DISPLAY PATIENT LISTS/RECORDS

### Frontend Display Components

#### [PatientRecords.jsx](frontend/src/components/PatientRecords.jsx)

- **Purpose**: Display all registered patients in table format
- **Data Source**: API endpoint `/record-officer/patients`
- **Fields Displayed**: Patient name, PID, Age/Sex, Phone, Visits count, Last Visit date
- **Features**:
  - Search support via `headerSearchValue` prop
  - Fetches data on component mount
  - Shows loading and empty states
  - Displays error toast notifications
- **Fetching Pattern**:
  ```javascript
  api.get(`/record-officer/patients${params ? `?${params}` : ""}`);
  ```

#### [Records.jsx](frontend/src/pages/Admin/Records.jsx)

- **Purpose**: Admin view of all patient records with search capability
- **Data Source**: API endpoint `/record-officer/patients?search={query}`
- **Fields Displayed**: Same as PatientRecords
- **Features**:
  - Search form with submit button
  - Dynamic patient count display
  - Lazy loading on component mount
  - Search persistence

#### [CreateVisit.jsx](frontend/src/components/CreateVisit.jsx)

- **Purpose**: Create new visit for existing patient
- **Data Source**:
  - Search: `/record-officer/patients/search` (supports pid, phone, nameDob)
  - Create: POST `/record-officer/visits`
- **Search Modes**: Patient ID, Phone Number, Name + DOB
- **Workflow**:
  1. Search and select patient
  2. Enter reason for visit and department
  3. Submit to create visit in WAITING_FOR_TRIAGE status
- **Departments Available**: General Outpatient, Pediatrics, OB/GYN, Surgery, Emergency

#### [NurseIntakeForm.jsx](frontend/src/components/NurseIntakeForm.jsx)

- **Purpose**: Nurse's data entry for triage
- **Displays**: Current patient information during triage assessment
- **Related to**: Patient vitals and medical assessment workflow

#### [ExaminationRecords.jsx](frontend/src/components/ExaminationRecords.jsx)

- **Purpose**: Display doctor examination records for patients
- **Features**: Links to examination SOAP notes and findings

#### [TriageRecords.jsx](frontend/src/components/TriageRecords.jsx)

- **Purpose**: Display triage assessment records
- **Features**: View historical triage assessments

#### [RecordOfficerDashboard.jsx](frontend/src/components/RecordOfficerDashboard.jsx)

- **Purpose**: Record officer's main dashboard
- **Shows**: Active patient lists and queue information

### Pages Displaying Patient Information

#### [Admin/Records.jsx](frontend/src/pages/Admin/Records.jsx)

- Full admin patient records view (as detailed above)

#### [Doctor/PatientsQueue.jsx](frontend/src/pages/Doctor/PatientsQueue.jsx)

- Shows patients in queue ready for consultation
- **ISSUE**: Uses hardcoded mock data instead of API

#### [Doctor/DoctorsDashboard.jsx](frontend/src/pages/Doctor/DoctorsDashboard.jsx)

- Doctor dashboard with stats: totalPatientsToday, awaitingTriage, awaitingConsultation, visitsEnded

#### [RecordOfficers/Dashboard.jsx](frontend/src/pages/RecordOfficers/Dashboard.jsx)

- Record officer dashboard

---

## 3. REGISTRATION & VISIT FORMS

### Patient Registration Form

#### [RegistrationForm.jsx](frontend/src/components/registration/RegistrationForm.jsx)

- **Type**: 4-step multi-step form
- **API Endpoint**: POST `/record-officer/register-patient`
- **Form Data Model**:
  ```javascript
  {
    // Step 1: Bio Data
    (lastName,
      firstName,
      otherNames,
      pid,
      gender,
      dob,
      age,
      nationality,
      civilStatus,
      tribe,
      religion,
      passport,
      // Step 2: Contact & Location
      phone,
      altPhone,
      email,
      address,
      state,
      lga,
      // Step 3: Statutory & Socio-Economic
      nin,
      nhisNumber,
      militaryNumber,
      education,
      regDate,
      regBy,
      // Step 4: Emergency Contact
      nokName,
      nokPhone,
      nokRelationship,
      nokAddress);
  }
  ```

#### Sub-components

- [StepOne.jsx](frontend/src/components/registration/StepOne.jsx) - Bio data entry
- [StepTwo.jsx](frontend/src/components/registration/StepTwo.jsx) - Contact & location
- [StepThree.jsx](frontend/src/components/registration/StepThree.jsx) - IDs & socio-economic
- [StepFour.jsx](frontend/src/components/registration/StepFour.jsx) - Next of kin

#### Alternative Registration (Record Officer)

- [RecordOfficers/MultistepForm](frontend/src/pages/RecordOfficers/MultistepForm/) - Alternative registration interface

### Visit Creation

#### [CreateVisit.jsx](frontend/src/components/CreateVisit.jsx)

- **API Endpoint**: POST `/record-officer/visits`
- **Request Body**:
  ```javascript
  {
    patient_id: string,
    reason_for_visit: string | null,
    department: string | null
  }
  ```
- **Response**:
  ```javascript
  {
    visit_id, patient_id, patient_name, visit_date, visit_time,
    visit_status: "WAITING_FOR_TRIAGE",
    triage_status: "PENDING",
    created_at
  }
  ```

---

## 4. VALIDATION RULES

### [registrationValidation.js](frontend/src/utils/registrationValidation.js)

#### Regex Patterns

```javascript
NAME_REGEX = /^[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF\s\-']+$/; // Names with accents
NIGERIAN_PHONE_REGEX = /^0[789]\d{9}$/; // 0803-0909 format
EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
NIN_REGEX = /^\d{11}$/; // 11 digits
NHIS_REGEX = /^[a-zA-Z0-9\-]{6,20}$/;
```

#### Step 1 Validation (Bio Data)

- **lastName**: Required, 2-50 chars, letters/spaces/hyphens only
- **firstName**: Required, 2-50 chars, letters/spaces/hyphens only
- **otherNames**: Optional, 2-100 chars if provided
- **dob**: Required, not future date, not >120 years old
- **gender**: Required
- **civilStatus**: Required
- **nationality**: Optional, 2-50 chars if provided
- **tribe**: Optional, 2-50 chars if provided

#### Step 2 Validation (Contact & Location)

- **phone**: Required, Nigerian format (0703-0909 + 8 digits)
- **altPhone**: Optional, Nigerian format if provided
- **email**: Optional, valid email format if provided
- **address**: Required, 5-200 chars
- **state**: Required
- **lga**: Required when state is selected

#### Step 3 Validation (IDs & Socio-Economic)

- **nin**: Optional, exactly 11 digits if provided
- **nhisNumber**: Optional, 6-20 alphanumeric/hyphens if provided
- **occupation**: Optional, 2-100 chars if provided

#### Step 4 Validation (Next of Kin)

- **nokName**: Required, 2-100 chars, letters/spaces/hyphens
- **nokRelationship**: Required
- **nokPhone**: Required, Nigerian format
- **nokAddress**: Required, 5-200 chars

---

## 5. BACKEND API ENDPOINTS

### [record_officer.py](backend/app/api/routes/record_officer.py)

#### GET /record-officer/patients

- **Auth**: ROLE_RECORD_OFFICER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN
- **Query Params**: `search` (optional)
- **Returns**: List of patients with id, pid, name, phone, dob, gender
- **Storage**: `store.list_patients(search)`

#### GET /record-officer/patients/search

- **Auth**: ROLE_RECORD_OFFICER, ROLE_ADMIN
- **Query Params**: `q` (min 1 char), `search_by` (pid|phone|nameDob)
- **Returns**: Filtered patient list
- **Storage**: `store.search_patients(q, search_by)`

#### POST /record-officer/register-patient

- **Auth**: ROLE_RECORD_OFFICER only
- **Request**: RegisterPatientBody (all form fields)
- **Returns**: `{ pid, id, ...patient data }`
- **Storage**: `store.register_patient(data, registered_by=staff_id)`
- **PID Format**: Generated as `PID-{YEAR}-{5-digit-sequence}`

#### POST /record-officer/visits

- **Auth**: ROLE_RECORD_OFFICER only
- **Request**: `{ patient_id, reason_for_visit, department }`
- **Returns**: Visit details with status and timestamps
- **Storage**: `store.create_visit(...)`
- **Default Status**: WAITING_FOR_TRIAGE

---

## 6. DATA STORAGE LAYERS

### [memory_store.py](backend/app/repositories/memory_store.py) (In-Memory)

- **Patients Dict**: `{patient_id: {patient_data}}`
- **Visits Dict**: `{visit_id: {visit_data}}`
- **PID Generation**: `PID-{YEAR}-{sequence}`
- **Visit ID Generation**: `VS-{YEAR}-{sequence}`
- **Methods**: register_patient, get_patient, list_patients, search_patients, create_visit

### [cliniq_db.py](backend/app/repositories/cliniq_db.py) (Database)

- **register_patient**: Stores patient in `patients` table, metadata in `patients_metadata`
- **get_patient**: Retrieves patient + metadata via JOIN
- **list_patients**: Returns up to 500 patients with search filtering
- **search_patients**: Supports pid, phone, and nameDob searches

### Database Schema

**patients** table:

- id (UUID), pid (VARCHAR UNIQUE), first_name, last_name, other_names
- date_of_birth, gender, age, passport_url, registered_by, created_at, updated_at

**patients_metadata** table:

- patient_id, email, phone, other_phone_number, address, state_of_origin, lga
- nationality, tribe, religion, education, civil_status, nin, nhis_number
- military_service_number, next_of_kin_name, next_of_kin_relationship, etc.

---

## 7. DATA FLOW DIAGRAM: Registration to Display

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PATIENT REGISTRATION FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

1. REGISTRATION (Record Officer)
   ┌──────────────────────────────────────────────────────────────────┐
   │  RegistrationForm.jsx (Multi-step)                              │
   │  ├─ Step 1: Bio Data (firstName, lastName, dob, gender, etc.)  │
   │  ├─ Step 2: Contact & Location (phone, email, address)         │
   │  ├─ Step 3: IDs (nin, nhis, occupation)                        │
   │  └─ Step 4: Next of Kin (nokName, nokPhone, etc.)             │
   │                                                                  │
   │  ↓ Validation via registrationValidation.js                     │
   │  ├─ validateStep1(): Name, DOB, Gender, Civil Status           │
   │  ├─ validateStep2(): Phone (Nigerian format), Address          │
   │  ├─ validateStep3(): NIN (11 digits), NHIS (6-20 chars)       │
   │  └─ validateStep4(): Next of Kin details                       │
   │                                                                  │
   │  ↓ Form Submission                                              │
   └──────────────────────────────────────────────────────────────────┘
           ↓
   ┌──────────────────────────────────────────────────────────────────┐
   │  POST /record-officer/register-patient                           │
   │  Body: {firstName, lastName, phone, email, address, nin, ...}   │
   └──────────────────────────────────────────────────────────────────┘
           ↓
   ┌──────────────────────────────────────────────────────────────────┐
   │  Backend: record_officer.py::register_patient()                 │
   │  ├─ Calls: store.register_patient(data, registered_by)         │
   │  └─ Returns: {pid, id, firstName, lastName, dob, created_at}  │
   └──────────────────────────────────────────────────────────────────┘
           ↓
   ┌──────────────────────────────────────────────────────────────────┐
   │  Storage Layer (cliniq_db.py or memory_store.py)               │
   │  ├─ Generate PID: PID-2026-00001                               │
   │  ├─ Insert into patients table/dict                            │
   │  ├─ Insert metadata into patients_metadata table/dict          │
   │  └─ Return patient record                                      │
   └──────────────────────────────────────────────────────────────────┘

2. VISIT CREATION (Record Officer)
   ┌──────────────────────────────────────────────────────────────────┐
   │  CreateVisit.jsx                                                │
   │  ├─ Search Patient: GET /record-officer/patients/search        │
   │  │    Options: By PID, Phone, or Name+DOB                     │
   │  │    ↓ Results displayed in dropdown                         │
   │  │                                                             │
   │  ├─ Select Patient + Enter Details:                           │
   │  │    ├─ Reason for Visit (optional)                          │
   │  │    └─ Department (General/Pediatrics/OB-GYN/Surgery/ER)   │
   │  │                                                             │
   │  └─ Create Visit: POST /record-officer/visits                │
   │       Body: {patient_id, reason_for_visit, department}       │
   └──────────────────────────────────────────────────────────────────┘
           ↓
   ┌──────────────────────────────────────────────────────────────────┐
   │  Backend: record_officer.py::create_visit()                    │
   │  ├─ Calls: store.create_visit(patient_id, ...)               │
   │  └─ Status: WAITING_FOR_TRIAGE, Triage: PENDING              │
   └──────────────────────────────────────────────────────────────────┘
           ↓
   ┌──────────────────────────────────────────────────────────────────┐
   │  Storage: Generate Visit ID (VS-2026-00001)                   │
   │  Status Flow: WAITING_FOR_TRIAGE → [TRIAGING] → ...          │
   └──────────────────────────────────────────────────────────────────┘

3. PATIENT DISPLAY (Various Roles)
   ┌──────────────────────────────────────────────────────────────────┐
   │  Display Components                                             │
   │  ├─ PatientRecords.jsx (All patients)                          │
   │  │    GET /record-officer/patients?search={query}             │
   │  │    Displayed: name, pid, age, sex, phone, visits, lastVisit│
   │  │                                                             │
   │  ├─ Records.jsx (Admin view)                                  │
   │  │    GET /record-officer/patients?search={query}             │
   │  │    With search form interface                              │
   │  │                                                             │
   │  └─ PatientsQueue.jsx (Doctor view) [HARDCODED - ISSUE]      │
   │       Should: GET /record-officer/visits or similar           │
   │       Currently: Uses hardcoded array queuePatients[]         │
   └──────────────────────────────────────────────────────────────────┘
           ↓
   ┌──────────────────────────────────────────────────────────────────┐
   │  Storage: retrieve patients via search filters                 │
   │  ├─ Search: By pid, firstName, lastName, phone               │
   │  └─ Returns: Limited to 500 records, sorted by created_at DESC│
   └──────────────────────────────────────────────────────────────────┘

```

---

## 8. CRITICAL DATA TRANSFORMATIONS

### Registration Data: Form → API Request → Storage

```javascript
// Form Data (RegistrationForm.jsx)
{
  firstName: "John",
  lastName: "Doe",
  phone: "08012345678",
  email: "john@example.com",
  // ... other fields
}
         ↓
// Backend normalization (cliniq_db.py::register_patient)
{
  first_name: "John",           // firstName → first_name
  last_name: "Doe",             // lastName → last_name
  metadata: {
    email: "john@example.com",  // email in metadata
    phone: "08012345678",       // phone in metadata
    other_phone_number: data.altPhone,
    address: data.address,
    state_of_origin: data.state,
    lga: data.lga,
    nin: data.nin,
    // ... etc
  }
}
         ↓
// Database Storage
patients table + patients_metadata table
         ↓
// API Response → Frontend
{
  id: "uuid",
  pid: "PID-2026-00001",
  firstName: "John",
  lastName: "Doe",
  dob: "1990-01-15",
  created_at: "2026-05-07T..."
}
```

---

## 9. KNOWN ISSUES & IMPROVEMENTS NEEDED

| Issue                                         | Location               | Impact                       | Priority |
| --------------------------------------------- | ---------------------- | ---------------------------- | -------- |
| Hardcoded mock data                           | PatientsQueue.jsx      | Doctor view shows wrong data | HIGH     |
| ActivePatientsList exports unused mock data   | ActivePatientsList.jsx | Code clutter, confusion      | MEDIUM   |
| No patient vitals display in records          | PatientRecords.jsx     | Missing vital signs info     | MEDIUM   |
| PatientsQueue doesn't fetch from API          | PatientsQueue.jsx      | Stale data                   | HIGH     |
| CreateVisit missing error handling edge cases | CreateVisit.jsx        | Poor UX on failures          | LOW      |

---

## 10. QUICK REFERENCE: Key File Locations

### Frontend Registration Path

- Entry: `frontend/src/components/registration/RegistrationForm.jsx`
- Validation: `frontend/src/utils/registrationValidation.js`
- Steps: `frontend/src/components/registration/Step{1-4}.jsx`

### Frontend Patient Display Path

- Main: `frontend/src/components/PatientRecords.jsx`
- Admin: `frontend/src/pages/Admin/Records.jsx`
- Doctor: `frontend/src/pages/Doctor/PatientsQueue.jsx` (NEEDS FIX)
- Create Visit: `frontend/src/components/CreateVisit.jsx`

### Backend API Routes

- Routes: `backend/app/api/routes/record_officer.py`
- Storage: `backend/app/repositories/cliniq_db.py` (DB) or `memory_store.py` (Memory)
- Schema: `backend/database/schema.py`

### Mock Data (To Remove/Update)

- `frontend/src/components/ActivePatientsList.jsx` - patientsList array
- `frontend/src/pages/Doctor/PatientsQueue.jsx` - queuePatients array
