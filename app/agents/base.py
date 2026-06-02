from abc import ABC, abstractmethod
from typing import Any

from app.agents.hermes import LLMClient
from app.memory.service import MemoryService
from app.research.schemas import AgentResult, AgentRole, MemoryType
import structlog


logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    role: AgentRole
    system_prompt: str

    def __init__(self, llm: LLMClient, memory: MemoryService) -> None:
        self.llm = llm
        self.memory = memory

    @abstractmethod
    def run(self, task: str, context: dict[str, Any]) -> AgentResult:
        raise NotImplementedError

    def _complete(self, task: str, context: dict[str, Any]) -> str:
        recalled = self.memory.recall(task, limit=5)
        memory_context = "\n".join(f"- {item.title}: {item.content[:300]}" for item in recalled)
        prompt = f"Task:\n{task}\n\nContext:\n{context}\n\nRelevant memory:\n{memory_context}"
        response = self.llm.complete(system=self.system_prompt, prompt=prompt)
        try:
            preview = response.replace("\n", " ")[:160]
        except Exception:
            preview = ""
        logger.info("llm_response", agent=self.role.value, prompt_len=len(prompt), response_len=len(response) if response else 0, preview=preview)
        return response

    def _remember(self, result: AgentResult, memory_type: MemoryType) -> None:
        self.memory.remember(
            memory_type=memory_type,
            source_agent=self.role,
            title=f"{self.role.value}: {result.summary[:80]}",
            content="\n".join([result.summary, *result.findings]),
            metadata={"artifacts": result.artifacts, "confidence": result.confidence},
        )
