# Backend

FastAPI API for the app. Default port **8000**.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and edit it. Then run:

```bash
uvicorn app.main:app --reload --port 8000
```

Routes under `/ai`, `/nlp`, and `/translate/chunk` call `AI_ENGINE_URL` (see `.env.example`). If nothing is listening there, those calls return **503** — the ML team ships that service separately; `../ai_engine` is reserved for them.

```bash
pytest
```
