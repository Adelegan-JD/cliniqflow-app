import os
from unittest import result
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,)

def test_connection() :
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database();"))
            print("Database Connected successfully")
            print("Result:", result.scalar())

            result = conn.execute(text("SELECT current_schema();"))
            print("Current Schema:", result.scalar())

            result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
            """))

            for row in result:
                print(row[0])

    except Exception as e:
        print("Database connection failed")
        print("Error:", str(e))


if __name__ == "__main__":
    test_connection()