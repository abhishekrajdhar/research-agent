from typing import Any

from app.orchestration.reflection import ReflectionEngine
from app.research.schemas import AgentResult, AgentRole, MemoryRecord, MemoryType


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        return None

    def refresh(self, obj: object) -> None:
        setattr(obj, "id", "reflection-1")


class FakeMemory:
    def __init__(self) -> None:
        self.records: list[MemoryRecord] = []

    def remember(
        self,
        *,
        memory_type: MemoryType,
        source_agent: AgentRole,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            memory_type=memory_type,
            source_agent=source_agent,
            title=title,
            content=content,
            metadata=metadata or {},
        )
        self.records.append(record)
        return record


def test_reflection_engine_writes_lessons_to_memory() -> None:
    session = FakeSession()
    memory = FakeMemory()
    engine = ReflectionEngine(session, memory)  # type: ignore[arg-type]
    result = AgentResult(agent=AgentRole.critic, summary="review", confidence=0.5)

    reflection_id = engine.reflect("task-1", [result])

    assert reflection_id == "reflection-1"
    assert session.added
    assert memory.records[0].memory_type == MemoryType.reflection
    assert "primary-source citation" in memory.records[0].content
