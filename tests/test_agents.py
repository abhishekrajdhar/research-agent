from typing import Any

from app.agents.hermes import LLMClient
from app.agents.planner import PlannerAgent
from app.research.schemas import AgentRole, MemoryRecord, MemoryType


class FakeLLM(LLMClient):
    def complete(self, system: str, prompt: str) -> str:
        return "generated plan"


class FakeMemory:
    def __init__(self) -> None:
        self.records: list[MemoryRecord] = []

    def recall(self, query: str, limit: int = 8) -> list[MemoryRecord]:
        return self.records[:limit]

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


def test_planner_generates_roadmap_and_memory() -> None:
    memory = FakeMemory()
    agent = PlannerAgent(FakeLLM(), memory)  # type: ignore[arg-type]

    result = agent.run("Plan a research task", {"question": "test"})

    assert result.agent == AgentRole.planner
    assert result.artifacts["roadmap"][0]["step"] == "literature_search"
    assert memory.records
    assert memory.records[0].memory_type == MemoryType.episodic
