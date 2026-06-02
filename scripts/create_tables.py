"""Create database tables for the project.

Run this script from the project root or via a one-off job on Render to initialize the DB.
"""
from app.db.session import engine, Base


def main() -> None:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done")


if __name__ == "__main__":
    main()
