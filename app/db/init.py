from app.db import models  # noqa: F401
from app.db.session import Base, engine


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
