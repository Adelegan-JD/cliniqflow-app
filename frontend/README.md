# CliniqFlow Frontend

A modern, role-based healthcare patient management and consultation platform built with React, Vite, and Tailwind CSS. CliniqFlow provides seamless workflows for administrative staff, nurses, doctors, and record officers to manage patient triage, consultations, and medical records.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [User Roles & Capabilities](#user-roles--capabilities)
3. [Getting Started](#getting-started)
4. [Installation](#installation)
5. [Running the Application](#running-the-application)
6. [Project Structure](#project-structure)
7. [Tech Stack](#tech-stack)
8. [Environment Setup](#environment-setup)

---

## Project Overview

CliniqFlow is a healthcare SaaS (Software-as-a-Service) platform designed to streamline patient care workflows from intake to consultation to record management. The platform enables:

- **Patient Registration & Triage**: Nurses conduct initial patient assessments and vitals collection.
- **Doctor Consultations**: Physicians review triaged patients and conduct examinations using voice and SOAP notes.
- **Medical Records Management**: Record officers maintain patient histories and documentation.
- **Administrative Oversight**: Admins manage users, settings, and system health monitoring.
- **AI-Assisted Diagnostics**: Integration with RAG (Retrieval-Augmented Generation) and ASR (Automatic Speech Recognition) for enhanced clinical decision support.

The application enforces strict role-based access control to ensure data security and appropriate clinical workflows.

---

## User Roles & Capabilities

### 🔐 **Administrator**

**Dashboard Route**: `/dashboard`

**Responsibilities & Access:**

- Manage system users (create, update, delete staff accounts)
- Configure application settings and system parameters
- View system health and performance metrics
- Manage role assignments and permissions
- Access comprehensive audit logs and activity reports
- Configure AI engine parameters and medical knowledge base

**Key Features:**

- User management panel with role-based provisioning
- System settings and configuration interface
- Help documentation and troubleshooting

---

### 👩‍⚕️ **Nurse**

**Dashboard Route**: `/nurse-dashboard`

**Responsibilities & Access:**

- Receive and manage patient triage queue
- Conduct patient intake and vital signs assessment
- Collect chief complaints and medical history
- Assign triage urgency levels (Normal, Urgent, Emergency)
- View completed triage records
- Monitor real-time triage queue status

**Key Features:**

- **Triage Queue**: Live queue of patients awaiting assessment
- **Triage Assessment Form**: Capture vitals (temperature, BP, heart rate, SpO₂, weight, height)
- **Vital Sign Analysis**: Automated urgency level evaluation (rule-based + AI-assisted)
- **Triage Records**: Historical view of all completed assessments
- **Quick Actions**: Start triage, view patient details, manage queue

---

### 👨‍⚕️ **Doctor**

**Dashboard Route**: `/doctors-dashboard`

**Responsibilities & Access:**

- Review consultation-ready patients from the queue
- Conduct virtual consultations with voice recording
- Create SOAP notes (Subjective, Objective, Assessment, Plan)
- Prescribe treatments and medications
- View patient medical history and previous records
- Monitor patients in consultation and completed visits

**Key Features:**

- **Patient Queue**: Patients at consultation stage ready for examination
- **Recording Session**: Voice-enabled consultation room with real-time transcription
- **SOAP Notes**: Structured clinical notes with AI assistance
- **Prescription Management**: Dosage validation and medication records
- **Patient Records**: Access full medical history and previous consultations
- **Dashboard Metrics**: Overview of queue status and consultation metrics

---

### 📋 **Record Officer**

**Dashboard Route**: `/record-officer`

**Responsibilities & Access:**

- Register new patients into the system
- Maintain and update patient records
- File and organize medical documentation
- Generate patient reports
- Verify patient information accuracy
- Archive and retrieve historical records

**Key Features:**

- **Patient Registration**: Collect demographics, contact info, emergency details
- **Records Management**: Organize and store patient files
- **Report Generation**: Create comprehensive patient summaries
- **Data Validation**: Ensure data integrity and consistency

---

## Getting Started

### Prerequisites

Ensure you have the following installed on your system:

- **Node.js** (v18 or higher)
- **pnpm** (v8 or higher) or **npm** (v9 or higher)
- **Git**

### Clone the Repository

```bash
git clone https://github.com/your-org/cliniqflow.git
cd cliniqflow/frontend
```

---

## Installation

### 1. Install Dependencies

Using **pnpm** (recommended for this project):

```bash
pnpm install
```

Or using **npm**:

```bash
npm install
```

### 2. Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory with the following variables:

```env
# Supabase Configuration
VITE_SUPABASE_URL=https://your-supabase-url.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# Backend API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Authentication Mode ('supabase' or 'dev')
VITE_AUTH_MODE=supabase

# Optional: Development bypass (set to false in production)
VITE_DEV_BYPASS_AUTH=false
```

**Note:** Ask your team lead or DevOps for the actual Supabase and backend credentials.

---

## Running the Application

### Development Server

Start the development server with hot-reloading:

```bash
pnpm dev
```

The application will be available at:

```
http://localhost:5173
```

### Production Build

Build the application for production:

```bash
pnpm build
```

Preview the production build locally:

```bash
pnpm preview
```

### Linting

Check code quality:

```bash
pnpm lint
```

---

## Project Structure

```
frontend/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── Sidebar.jsx       # Navigation sidebar
│   │   ├── TriageForm.jsx    # Triage assessment form
│   │   ├── Navbar.jsx        # Top navigation bar
│   │   └── ...
│   ├── pages/                # Page-level components by role
│   │   ├── Admin/            # Admin dashboard pages
│   │   ├── Nurse/            # Nurse workflow pages
│   │   ├── Doctor/           # Doctor consultation pages
│   │   ├── RecordOfficers/   # Record management pages
│   │   ├── Authentication/   # Login and auth pages
│   │   └── Home.jsx          # Landing page
│   ├── contexts/             # React context (Auth, etc.)
│   ├── hooks/                # Custom React hooks
│   ├── store/                # Zustand state management
│   ├── utils/                # Utility functions and API client
│   ├── data/                 # Static data (states, LGAs, etc.)
│   ├── styles/               # Global and component styles
│   ├── App.jsx               # Main app component with routing
│   ├── main.jsx              # React entry point
│   └── index.css             # Global Tailwind imports
│
├── public/                   # Static assets
├── package.json              # Dependencies and scripts
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── eslint.config.js          # ESLint configuration
└── README.md                 # This file
```

---

## Tech Stack

| Technology          | Purpose                            |
| ------------------- | ---------------------------------- |
| **React 19**        | UI library                         |
| **Vite**            | Build tool and dev server          |
| **React Router v7** | Client-side routing                |
| **Tailwind CSS v4** | Utility-first styling              |
| **Zustand**         | State management                   |
| **Supabase JS**     | Authentication & real-time updates |
| **Lucide React**    | Icon library                       |
| **React Toastify**  | Toast notifications                |
| **Zod**             | Schema validation                  |

---

## Environment Setup

### Backend Connection

Ensure the backend API is running before starting the frontend:

```bash
cd backend
uvicorn app.main:app --reload
```

The backend should be accessible at `http://localhost:8000` (configurable via `VITE_API_BASE_URL`).

### Supabase Configuration

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Retrieve your project URL and anonymous API key
3. Add them to `.env.local` as shown in the [Environment Variables](#2-configure-environment-variables) section

### Authentication Flow

The application uses JWT-based authentication with role-based access control:

1. User logs in via `/login` with email and password
2. Credentials are authenticated against the backend
3. Backend issues JWT tokens (access + refresh)
4. Frontend stores tokens and enforces role-based routing
5. All API requests include the JWT in the `Authorization` header

**Protected Routes:**

- `/dashboard` - Admin only
- `/nurse-dashboard` - Nurse only
- `/doctors-dashboard` - Doctor only
- `/record-officer` - Record Officer only

Unauthorized access attempts redirect users to their role-based dashboard.

---

## Common Development Tasks

### Adding a New Page

1. Create a new file in `src/pages/{Role}/{PageName}.jsx`
2. Export the component as default
3. Add the route in `src/App.jsx` under the appropriate role layout
4. Add navigation link in the sidebar if needed

### Creating a Reusable Component

1. Create a new file in `src/components/{ComponentName}.jsx`
2. Export as default or named export
3. Use in pages or other components as needed
4. Document prop types with JSDoc comments

### Making API Calls

Use the centralized API wrapper at `src/utils/api.js`:

```javascript
import { api } from "../../utils/api";

// GET request
const data = await api.get("/endpoint");

// POST request
const result = await api.post("/endpoint", { data });

// PUT request
await api.put("/endpoint/{id}", { data });

// DELETE request
await api.delete("/endpoint/{id}");
```

### State Management

Use Zustand stores in `src/store/`:

```javascript
import { useAuthStore } from "../store/authStore";

export function MyComponent() {
  const { user, logout } = useAuthStore();
  // ...
}
```

---

## Troubleshooting

### "Cannot find module" errors

```bash
pnpm install
```

### Vite port already in use

```bash
pnpm dev -- --port 5174
```

### Build errors

Clear cache and reinstall:

```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
pnpm build
```

### Backend connection issues

- Ensure backend is running: `uvicorn app.main:app --reload`
- Check `VITE_API_BASE_URL` in `.env.local`
- Verify CORS is enabled in backend

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and commit: `git commit -m "Add your feature"`
3. Push to the branch: `git push origin feature/your-feature`
4. Open a Pull Request with a clear description

---

## Support & Documentation

For detailed backend documentation, see `../backend/README.md`.

For issues, questions, or suggestions, contact the development team.

---

**Last Updated:** May 2026
# CliniqFlow Frontend

The frontend is the role-based web application for CliniqFlow. It provides the user experience for record officers, nurses, doctors, and admins to register patients, manage queues, capture triage, and document visits. It talks to the backend API and uses Supabase for authentication.

## What this frontend is responsible for

- Role-based UI and navigation (admin, record officer, nurse, doctor)
- Patient registration and search
- Visit creation and queue views
- Nurse triage forms and triage records
- Doctor encounter flows (SOAP summaries, exam records)
- Admin dashboards and user management screens

## Tech stack

- React 19 + React Router
- Vite for dev server and bundling
- Tailwind CSS for styling
- Zustand for client state
- Zod for validation
- Supabase JS client for auth
- React Toastify for notifications

## API integration

- API base URL is read from `VITE_API_URL`
- Requests include `Authorization: Bearer <token>` pulled from the user session.
- Supabase client configuration lives in `src/utils/supabaseClient.js`.

## Environment variables

Create a `frontend/.env` file with:

- VITE_API_URL: backend base URL 
- VITE_SUPABASE_URL: Supabase project URL
- VITE_SUPABASE_ANON_KEY: Supabase anon key

## Folder structure

```
frontend/
├── public/
├── src/
│   ├── components/     # reusable UI components
│   ├── contexts/       # auth and app contexts
│   ├── hooks/          # custom hooks
│   ├── pages/          # role-based screens
│   ├── store/          # Zustand stores
│   ├── utils/          # API helpers, Supabase client
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── package.json
└── README.md
```

## Run locally (Windows PowerShell)

```
cd frontend
pnpm install
pnpm dev
```

## Scripts

- pnpm dev: start the Vite dev server
- pnpm build: production build
- pnpm preview: preview the production build
- pnpm lint: run ESLint
