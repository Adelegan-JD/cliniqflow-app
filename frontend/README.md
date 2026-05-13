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
