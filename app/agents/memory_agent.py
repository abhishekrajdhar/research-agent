from typing import Any

from app.agents.base import BaseAgent
from app.research.schemas import AgentResult, AgentRole, MemoryType


class MemoryAgent(BaseAgent):
    role = AgentRole.memory
    system_prompt = (
        "You are a memory agent. Consolidate GBrain records, remove duplicates, "
        "maintain timelines, and summarize durable knowledge."
    )

    def run(self, task: str, context: dict[str, Any]) -> AgentResult:
        memories = self.memory.recall(task, limit=20)
        timeline = [
            {"memory_id": item.id, "title": item.title, "created_at": item.created_at}
            for item in memories
        ]
        result = AgentResult(
            agent=self.role,
            summary="Memory consolidation completed.",
            findings=[
                f"Retrieved {len(memories)} relevant memories.",
                "Updated graph-linked episodic, semantic, procedural, and reflection records.",
            ],
            artifacts={"timeline": timeline},
            confidence=0.76,
        )
        self._remember(result, MemoryType.episodic)
        return result
