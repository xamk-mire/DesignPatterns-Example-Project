"""Database engine and connectivity check."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from infrastructure.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def check_database() -> bool:
    try:
        print("Checking database connection...")
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection successful")
        return True
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        return False
