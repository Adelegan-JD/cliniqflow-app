# Backend

FastAPI service. Runs on **port 8000** by default.

## Run locally

```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`  
**Windows (cmd):** `.\.venv\Scripts\activate.bat`

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- **Docs:** http://127.0.0.1:8000/docs  
- **Health:** http://127.0.0.1:8000/health (`persistence` is `postgres` only if `DATABASE_URL` is set)


## Tests

```bash
pytest
```
