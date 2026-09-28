"""Replace dashboard rows with the shared Lab Site seed. Does not touch greenhouse_test."""

from infrastructure.db import SessionLocal
from infrastructure.dev_seed import seed_database, truncate_business_tables


def main() -> None:
    session = SessionLocal()
    try:
        truncate_business_tables(session)
        seed = seed_database(session)
    finally:
        session.close()
    print(f"Reset dashboard database. Lab Site id {seed.location_id}.")


if __name__ == "__main__":
    main()
