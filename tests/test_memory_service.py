from datetime import datetime, timezone

from app.memory.service import MemoryService
from app.research.schemas import AgentRole, MemoryRecord, MemoryType


class FakeGBrain:
    def __init__(self) -> None:
        self.stored: MemoryRecord | None = None

    def enrich(self, record: MemoryRecord) -> MemoryRecord:
        return record

    def retrieve(self, query: str, limit: int = 8) -> list[MemoryRecord]:
        return []

    def store(self, record: MemoryRecord) -> MemoryRecord:
        self.stored = record
        return record


class FakeSession:
    pass


def test_memory_service_converts_metadata_to_json_safe_values() -> None:
    gbrain = FakeGBrain()
    service = MemoryService(FakeSession(), gbrain)  # type: ignore[arg-type]
    created_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    record = service.remember(
        memory_type=MemoryType.episodic,
        source_agent=AgentRole.memory,
        title="timeline",
        content="memory timeline",
        metadata={"timeline": [{"created_at": created_at}]},
    )

    timeline = record.metadata["timeline"]
    assert isinstance(timeline, list)
    assert isinstance(timeline[0], dict)
    assert timeline[0]["created_at"] == "2026-06-02T12:00:00+00:00"
