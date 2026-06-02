from typing import Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.models import MemoryORM, TaskORM
from app.db.session import get_session
from app.monitoring.metrics import PIPELINES_COMPLETED, PIPELINES_FAILED, TASKS_CREATED, health_snapshot, render_metrics
from app.orchestration.pipeline import ResearchPipeline
from app.research.schemas import MemoryRecord, ResearchPipelineResult, ResearchRequest

router = APIRouter()


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, int | str]:
    return health_snapshot(session)


@router.post("/research", response_model=ResearchPipelineResult)
def run_research(request: ResearchRequest, session: Session = Depends(get_session)) -> ResearchPipelineResult:
    TASKS_CREATED.inc()
    try:
        result = ResearchPipeline(session).run(request)
    except Exception:
        PIPELINES_FAILED.inc()
        raise
    PIPELINES_COMPLETED.inc()
    return result


@router.get("/tasks")
def list_tasks(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    rows = session.query(TaskORM).order_by(TaskORM.created_at.desc()).limit(50).all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "status": row.status,
            "priority": row.priority,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


@router.get("/memory", response_model=list[MemoryRecord])
def list_memory(session: Session = Depends(get_session), limit: int = 50) -> list[MemoryRecord]:
    rows = session.query(MemoryORM).order_by(MemoryORM.created_at.desc()).limit(limit).all()
    return [
        MemoryRecord(
            id=row.id,
            memory_type=row.memory_type,
            source_agent=row.source_agent,
            title=row.title,
            content=row.content,
            entities=row.entities,
            relations=row.relations,
            metadata=row.metadata_,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/metrics")
def metrics(session: Session = Depends(get_session)) -> Response:
    return Response(render_metrics(session), media_type="text/plain; version=0.0.4")
