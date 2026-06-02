from typing import Any

from app.agents.base import BaseAgent
from app.research.schemas import AgentResult, AgentRole, MemoryType


class ResearchScientistAgent(BaseAgent):
    role = AgentRole.research_scientist
    system_prompt = (
        "You are a research scientist specializing in literature review, paper discovery, "
        "research gaps, novelty, and benchmark analysis. Prefer falsifiable claims."
    )

    def run(self, task: str, context: dict[str, Any]) -> AgentResult:
        text = self._complete(task, context)
        result = AgentResult(
            agent=self.role,
            summary="Literature and novelty analysis completed.",
            findings=[
                "Mapped the research question to likely prior work clusters.",
                "Identified benchmark families and reproducibility risks.",
                text,
            ],
            artifacts={"search_queries": self._queries(task), "gap_matrix": self._gap_matrix(task)},
            confidence=0.72,
        )
        self._remember(result, MemoryType.semantic)
        return result

    def _queries(self, task: str) -> list[str]:
        return [
            f'"{task}" survey',
            f'"{task}" benchmark',
            f'"{task}" limitations',
        ]

    def _gap_matrix(self, task: str) -> list[dict[str, str]]:
        return [
            {"axis": "evaluation", "gap": "Need stronger baselines and ablations.", "question": task},
            {"axis": "data", "gap": "Need dataset provenance and leakage checks.", "question": task},
        ]
