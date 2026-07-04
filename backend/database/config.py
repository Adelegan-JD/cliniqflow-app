# import os

# from dotenv import load_dotenv
# from sqlalchemy import create_engine, text

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")

# engine = (
#     create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
# )


# def test_connection() -> None:
#     if engine is None:
#         print("DATABASE_URL is not set.")
#         return
#     try:
#         with engine.connect() as conn:
#             result = conn.execute(text("SELECT current_database();"))
#             print("Database connected:", result.scalar())
#     except Exception as e:
#         print("Database connection failed:", str(e))


# if __name__ == "__main__":
#     test_connection()



import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Optimized configuration for Supabase connection poolers
engine = (
    create_engine(
        DATABASE_URL, 
        pool_size=5,          # Keep the pool small and efficient
        max_overflow=10, 
        pool_recycle=60,      # Recycle connections every 60 seconds
        pool_pre_ping=True    # Safely test connection before queries
    ) if DATABASE_URL else None
)


def test_connection() -> None:
    if engine is None:
        print("DATABASE_URL is not set.")
        return
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database();"))
            print("Database connected:", result.scalar())
    except Exception as e:
        print("Database connection failed:", str(e))


if __name__ == "__main__":
    test_connection()
