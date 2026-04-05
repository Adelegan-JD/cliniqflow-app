
# CliniqFlow - Healthcare AI Assistant for Modern Medical Practice

## What is This Project?

CliniqFlow is an intelligent software system that helps healthcare professionals (doctors, nurses, and medical practitioners) organize and analyze patient information quickly and accurately. It takes unstructured patient notes from consultations and transforms them into organized, actionable medical data that follows international healthcare standards.

**Main Purpose:** Improve healthcare delivery by automating the organization of patient information, enabling better decision-making, faster documentation, and improved patient care across all age groups and demographics.

**Technology Used:**
- **FastAPI:** A modern web framework for building high-performance APIs
- **Python 3.8+:** The programming language that powers the application
- **OpenAI API:** Optional AI integration for advanced language understanding
- **Pydantic:** Data validation and type checking framework

---

## What Does It Do?

### For Nurses & Triage Personnel: Rapid Patient Assessment
- Enter a patient's vital signs (temperature, heart rate, breathing rate, blood pressure, oxygen level, etc.)
- Get an immediate triage recommendation:
  - 🟢 **Green (Normal):** Patient is stable, routine care appropriate
  - 🟡 **Yellow (Urgent):** Patient needs attention soon, but not immediately critical
  - 🔴 **Red (Emergency):** Patient needs immediate medical attention

### For Doctors & Medical Practitioners: Comprehensive Patient Documentation
- Input a patient consultation (conversation, notes, observations)
- System automatically:
  - Extracts all mentioned symptoms with severity and onset information
  - Identifies relevant medical history and family history
  - Organizes vital signs and measurements
  - Flags concerning clinical findings that may need immediate attention
  - Generates a complete SOAP note (Subjective, Objective, Assessment, Plan) in standard medical format
  - Provides confidence scores indicating how reliable each extracted piece of information is

---

## How to Get Started

### Prerequisites
You need Python 3.8 or higher installed. If you don't have it, download it from [python.org](https://www.python.org/downloads/).

### Step 1: Get the Project Files
Clone or download this repository to your local machine:
```bash
git clone <repository-url>
cd kenny_code_only
```

### Step 2: Create a Virtual Environment
A virtual environment isolates this project's dependencies from other Python projects on your computer.

**For Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**For Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**For macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables (Optional but Recommended)
Create a `.env` file in the project root directory:
```
OPENAI_API_KEY=your-openai-api-key-here
```

To get an OpenAI API key:
- Visit [openai.com](https://openai.com)
- Create an account or sign in
- Go to API settings and create a new API key
- Copy the key into your `.env` file

**Note:** The system can work with basic extraction without an API key, but AI-powered analysis requires this key.

### Step 5: Run the Application
```bash
cd app/nlp/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Access the Interface
Open your browser and go to: **http://127.0.0.1:8000/docs**

You'll see an interactive API documentation interface (Swagger UI) where you can test all available endpoints.

---

## How to Use CliniqFlow

### Scenario 1: Triage Personnel Rapid Assessment
A patient arrives at the clinic. The triage nurse quickly measures vital signs and enters them:

**Endpoint:** `/nlp/vitals-urgency`

**Example Request:**
```json
{
  "patient_age": "45 years",
  "patient_sex": "female",
  "temperature": 38.9,
  "heart_rate": 115,
  "respiratory_rate": 24,
  "oxygen_saturation": 92,
  "blood_pressure_systolic": 145,
  "blood_pressure_diastolic": 92,
  "weight_kg": 68,
  "height_cm": 165
}
```

**System Response:** Urgency level (Green/Yellow/Red) with clinical reasoning

---

### Scenario 2: Doctor's Comprehensive Patient Processing
A doctor completes a patient consultation and needs documentation:

**Endpoint:** `/nlp/process`

**Example Request:**
```json
{
  "transcript": "Patient reports 3 days of fever, persistent cough, and difficulty breathing. Temperature was 39°C this morning. No known allergies. Family history of hypertension.",
  "patient_age": "52 years",
  "patient_sex": "male",
  "session_id": "session_123"
}
```

**System Response:** 
- Extracted symptoms with severity ratings
- Identified vital signs
- Medical history summary
- Complete SOAP note
- Clinical flags (if any concerning findings)
- Confidence scores for each extracted element

---

## Project Architecture Overview

```
kenny_code_only/
├── app/
│   └── nlp/
│       ├── api/
│       │   ├── main.py              # Application entry point
│       │   └── nlp_routes.py        # API endpoints
│       ├── models/
│       │   └── clinical_schema.py   # Data structure definitions
│       └── src/
│           ├── symptom_extractor.py      # Text analysis engine
│           ├── soap_formatter.py         # Medical note generator
│           ├── urgency_scorer.py         # Triage calculator
│           ├── confidence_calculator.py  # Data reliability scorer
│           └── validators.py            # Data quality checks
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## Core Features Explained

### 1. **Intelligent Text Processing**
The system analyzes patient consultation text using two approaches:
- **Rule-Based:** Looks for known medical keywords and patterns (fast, reliable)
- **AI-Powered:** Uses OpenAI's language models for contextual understanding (more accurate for complex cases)
- **Hybrid:** Combines both methods for optimal results

### 2. **Triage & Urgency Assessment**
Evaluates vital signs against age-appropriate normal ranges and provides:
- Color-coded urgency levels for quick decision-making
- Specific reasons for urgency classification
- Support for patients of all ages (pediatric through geriatric)

### 3. **Structured Medical Documentation**
Automatically generates SOAP notes following international medical standards:
- **S (Subjective):** What the patient reports
- **O (Objective):** Measured vital signs and physical findings
- **A (Assessment):** Clinical interpretation
- **P (Plan):** Recommended next steps

### 4. **Confidence Scoring**
Each extracted piece of information receives a confidence score (0-100%), indicating how reliable the data is

### 5. **Safety & Quality Checks**
- Identifies missing critical information
- Flags abnormal vital signs
- Detects potential data quality issues
- Never Auto-diagnoses (system provides data, not medical decisions)

---

## Running Tests

To verify the installation and run tests:
```bash
pytest tests/ -v
```

Tests are located in the `tests/` directory and cover all major modules.

---

## Development Guidelines

### Code Quality
- Use **black** for code formatting consistency
- Use **ruff** for linting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Include docstrings for modules, classes, and functions

### Adding New Features
1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Write tests first (TDD approach recommended)
3. Implement the feature
4. Ensure all tests pass
5. Submit a pull request

### Updating Dependencies
- Update `requirements.txt` when adding new packages
- Test thoroughly before committing
- Document any breaking changes

---

## Who Can Use CliniqFlow?

**Healthcare Professionals** including:
- **Nurses & Triage Personnel** - For rapid patient assessment and triage decisions
- **Doctors & Physicians** - For structured documentation and clinical decision support
- **Healthcare Administrators** - For improved record-keeping and operational efficiency
- **Medical Students & Residents** - For learning proper medical documentation

**Applicable Settings:**
- Primary care clinics
- Hospital emergency departments
- Urgent care centers
- Telemedicine platforms
- Healthcare training institutions

**Patient Demographics:**
- All ages (pediatric, adult, geriatric)
- All geographic regions
- Multiple languages and contexts (system is extensible)

---

## Limitations & Important Notes

**This is a Decision Support Tool, Not a Diagnostic Tool**
- CliniqFlow helps organize information, not diagnose conditions
- Final medical decisions rest with qualified healthcare professionals
- System confidence scores indicate data reliability, not medical certainty
- Always use clinical judgment in conjunction with this tool

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'openai'"
**Solution:** Run `pip install -r requirements.txt` to install all dependencies

### Issue: Fast API won't start
**Solution:** 
- Ensure you're in the correct directory: `app/nlp/api`
- Check port 8000 isn't already in use: Change to `--port 8001` if needed
- Verify Python environment is activated

### Issue: API works but returns errors for every query
**Solution:**
- Check if `.env` file has a valid OpenAI API key (if using AI features)
- Try with just rule-based extraction (doesn't require API key)

### Issue: Unusual results from symptom extraction
**Solution:**
- Check confidence scores (may be low for unclear input)
- Try reformatting patient transcript with clearer language
- Review extraction warnings in the response

---

