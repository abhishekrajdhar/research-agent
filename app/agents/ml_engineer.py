from typing import Any

from app.agents.base import BaseAgent
from app.research.schemas import AgentResult, AgentRole, MemoryType


class MLEngineerAgent(BaseAgent):
    role = AgentRole.ml_engineer
    system_prompt = (
        "You are an ML engineer responsible for datasets, training, evaluation, "
        "experiment execution, and reproducibility."
    )

    def run(self, task: str, context: dict[str, Any]) -> AgentResult:
        text = self._complete(task, context)
        result = AgentResult(
            agent=self.role,
            summary="Experiment plan and execution scaffold prepared.",
            findings=[
                "Defined dataset preparation, deterministic seeds, metrics, and artifact tracking.",
                "Created a reproducibility checklist for the proposed experiment.",
                text,
            ],
            artifacts={
                "experiment_template": {
                    "seed": 42,
                    "metrics": ["accuracy", "f1", "latency_ms", "cost_per_run"],
                    "stages": ["prepare_data", "train", "evaluate", "package_artifacts"],
                }
            },
            confidence=0.7,
        )
        self._remember(result, MemoryType.procedural)
        return result
