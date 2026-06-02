from pathlib import Path
import sys

# Ensure project root is in sys.path so `app` imports work when running this script directly.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from app.db.session import engine, Base
except Exception as exc:  # pragma: no cover - helpful runtime message
    raise SystemExit(f"Failed to import project modules: {exc}\nMake sure you run this from the project root.")


def main() -> None:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done")


if __name__ == "__main__":
    main()
