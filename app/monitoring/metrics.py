from prometheus_client import Counter, Gauge, generate_latest
from sqlalchemy.orm import Session

from app.db.models import MemoryORM, TaskORM

TASKS_CREATED = Counter("research_lab_tasks_created_total", "Total research tasks created")
PIPELINES_COMPLETED = Counter("research_lab_pipelines_completed_total", "Completed pipelines")
PIPELINES_FAILED = Counter("research_lab_pipelines_failed_total", "Failed pipelines")
MEMORY_RECORDS = Gauge("research_lab_memory_records", "Total memory records")


def collect_memory_metrics(session: Session) -> None:
    MEMORY_RECORDS.set(session.query(MemoryORM).count())


def render_metrics(session: Session) -> bytes:
    collect_memory_metrics(session)
    return generate_latest()


def health_snapshot(session: Session) -> dict[str, int | str]:
    return {
        "status": "ok",
        "tasks": session.query(TaskORM).count(),
        "memories": session.query(MemoryORM).count(),
    }
