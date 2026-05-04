from database.config import engine

if engine is not None:
    from app.repositories.cliniq_db import store
else:
    from app.repositories.memory_store import store

__all__ = ["store"]
