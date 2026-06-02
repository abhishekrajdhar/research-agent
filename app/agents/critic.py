from typing import Any

from app.agents.base import BaseAgent
from app.research.schemas import AgentResult, AgentRole, MemoryType


class CriticAgent(BaseAgent):
    role = AgentRole.critic
    system_prompt = (
        "You are a critic agent. Detect hallucinations, verify citation quality, "
        "challenge assumptions, evaluate novelty, and flag weak evidence."
    )

    def run(self, task: str, context: dict[str, Any]) -> AgentResult:
        text = self._complete(task, context)
        risks = [
            "Citation claims must be verified against primary sources before publication.",
            "Novelty is provisional until competing methods are searched and compared.",
            "Benchmarks require leakage checks, baseline parity, and confidence intervals.",
        ]
        result = AgentResult(
            agent=self.role,
            summary="Research quality review completed.",
            findings=[*risks, text],
            artifacts={"risk_register": risks, "decision": "revise_before_publish"},
            confidence=0.82,
        )
        self._remember(result, MemoryType.reflection)
        return result
