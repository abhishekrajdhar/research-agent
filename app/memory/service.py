from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.memory.gbrain import GBrainClient, RemoteGBrainProxy
from app.research.schemas import AgentRole, MemoryRecord, MemoryType


class MemoryService:
    def __init__(self, session: Session, gbrain: GBrainClient | None = None) -> None:
        self.gbrain = gbrain or RemoteGBrainProxy(session=session, settings=get_settings())

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
            metadata=self._json_safe(metadata or {}),
        )
        return self.gbrain.store(record)

    def recall(self, query: str, limit: int = 8) -> list[MemoryRecord]:
        return self.gbrain.retrieve(query=query, limit=limit)

    def _json_safe(self, value: dict[str, Any]) -> dict[str, Any]:
        encoded = jsonable_encoder(value)
        if not isinstance(encoded, dict):
            return {}
        return encoded
