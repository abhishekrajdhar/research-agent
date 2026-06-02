from typing import Any

from app.agents.base import BaseAgent
from app.research.schemas import AgentResult, AgentRole, MemoryType


class PlannerAgent(BaseAgent):
    role = AgentRole.planner
    system_prompt = (
        "You are a planner agent. Decompose work, prioritize roadmap steps, "
        "estimate resources, and preserve dependencies."
    )

    def run(self, task: str, context: dict[str, Any]) -> AgentResult:
        text = self._complete(task, context)
        roadmap = [
            {"step": "literature_search", "priority": "high", "owner": "research_scientist"},
            {"step": "gap_analysis", "priority": "high", "owner": "research_scientist"},
            {"step": "hypothesis_generation", "priority": "high", "owner": "research_scientist"},
            {"step": "experiment_design", "priority": "high", "owner": "ml_engineer"},
            {"step": "review_and_memory_update", "priority": "high", "owner": "critic"},
        ]
        result = AgentResult(
            agent=self.role,
            summary="Roadmap generated and prioritized.",
            findings=["Converted the research goal into an executable pipeline.", text],
            artifacts={"roadmap": roadmap},
            confidence=0.78,
        )
        self._remember(result, MemoryType.episodic)
        return result
