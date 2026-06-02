"""API router for the research lab."""

from typing import Any
from threading import Thread

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.models import MemoryORM, TaskORM
from app.db.session import get_session, SessionLocal
from app.monitoring.metrics import (
    PIPELINES_COMPLETED,
    PIPELINES_FAILED,
    TASKS_CREATED,
    health_snapshot,
    render_metrics,
)
from app.orchestration.pipeline import ResearchPipeline
from app.research.schemas import MemoryRecord, ResearchPipelineResult, ResearchRequest

router = APIRouter()


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, int | str]:
    return health_snapshot(session)


def _run_pipeline_background(request: ResearchRequest, task_id: str) -> None:
    # create a new DB session for the worker thread
    with SessionLocal() as session:
        try:
            ResearchPipeline(session).run(request, existing_task_id=task_id)
            PIPELINES_COMPLETED.inc()
        except Exception:
            PIPELINES_FAILED.inc()
            # ensure task marked failed
            t = session.get(TaskORM, task_id)
            if t is not None:
                t.status = "failed"
                session.add(t)
                session.commit()
            raise


@router.post("/research", status_code=202)
def run_research(request: ResearchRequest, session: Session = Depends(get_session)) -> dict[str, str]:
    TASKS_CREATED.inc()
    task = TaskORM(title=request.question, status="queued", payload=request.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)

    # start background thread (it will create its own session)
    thread = Thread(target=_run_pipeline_background, args=(request, task.id), daemon=True)
    thread.start()
    return {"task_id": task.id}


@router.get("/tasks/{task_id}")
def get_task(task_id: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    task = session.get(TaskORM, task_id)
    if task is None:
        return {"error": "not_found"}
    return {"id": task.id, "status": task.status, "result": task.result or {}, "title": task.title}


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
