from sqlalchemy.orm import Session

from app.db.models import ReflectionORM
from app.memory.service import MemoryService
from app.research.schemas import AgentResult, AgentRole, MemoryType


class ReflectionEngine:
    def __init__(self, session: Session, memory: MemoryService) -> None:
        self.session = session
        self.memory = memory

    def reflect(self, task_id: str, results: list[AgentResult]) -> str:
        low_confidence = [result for result in results if result.confidence < 0.75]
        mistakes = [
            "One or more steps have provisional confidence and need evidence hardening."
            for _ in low_confidence[:1]
        ]
        lessons = [
            "Route literature claims through the critic before treating them as durable facts.",
            "Store experiment templates as procedural memory to improve reproducibility.",
            "Keep every pipeline stage linked to episodic memory for auditability.",
        ]
        improvements = [
            "Add primary-source citation verification before paper drafting.",
            "Schedule benchmark replication when ML experiment artifacts are incomplete.",
        ]
        outcome_score = "needs_review" if low_confidence else "strong"
        reflection = ReflectionORM(
            task_id=task_id,
            outcome_score=outcome_score,
            lessons=lessons,
            mistakes=mistakes,
            improvements=improvements,
        )
        self.session.add(reflection)
        self.session.commit()
        self.session.refresh(reflection)
        self.memory.remember(
            memory_type=MemoryType.reflection,
            source_agent=AgentRole.memory,
            title=f"Reflection for task {task_id}",
            content="\n".join([*lessons, *mistakes, *improvements]),
            metadata={"task_id": task_id, "outcome_score": outcome_score},
        )
        return reflection.id
