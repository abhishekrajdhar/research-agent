import re
from typing import Protocol

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import MemoryORM
from app.research.schemas import AgentRole, Entity, MemoryRecord, MemoryType, Relation


class GBrainClient(Protocol):
    def enrich(self, record: MemoryRecord) -> MemoryRecord:
        ...

    def retrieve(self, query: str, limit: int = 8) -> list[MemoryRecord]:
        ...

    def store(self, record: MemoryRecord) -> MemoryRecord:
        ...


class LocalGBrain:
    """Graph-first local memory implementation compatible with a future GBrain service."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.qdrant = QdrantClient(url=settings.qdrant_url, prefer_grpc=False)
        self._ensure_collection()

    def enrich(self, record: MemoryRecord) -> MemoryRecord:
        entities = record.entities or self._extract_entities(record.content)
        relations = record.relations or self._extract_relations(record.content, entities)
        record.entities = entities
        record.relations = relations
        return record

    def store(self, record: MemoryRecord) -> MemoryRecord:
        enriched = self.enrich(record)
        orm = MemoryORM(
            memory_type=enriched.memory_type.value,
            source_agent=enriched.source_agent.value,
            title=enriched.title,
            content=enriched.content,
            entities=[entity.model_dump() for entity in enriched.entities],
            relations=[relation.model_dump() for relation in enriched.relations],
            metadata_=enriched.metadata,
        )
        self.session.add(orm)
        self.session.commit()
        self.session.refresh(orm)
        enriched.id = orm.id
        enriched.created_at = orm.created_at
        self._index_vector(enriched)
        return enriched

    def retrieve(self, query: str, limit: int = 8) -> list[MemoryRecord]:
        terms = [term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", query)]
        rows = self.session.query(MemoryORM).order_by(MemoryORM.created_at.desc()).limit(100).all()
        scored: list[tuple[int, MemoryORM]] = []
        for row in rows:
            haystack = f"{row.title} {row.content}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score > 0 or not terms:
                scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [self._from_orm(row) for _, row in scored[:limit]]

    def _ensure_collection(self) -> None:
        existing = {collection.name for collection in self.qdrant.get_collections().collections}
        if self.settings.qdrant_collection not in existing:
            self.qdrant.create_collection(
                collection_name=self.settings.qdrant_collection,
                vectors_config=VectorParams(size=32, distance=Distance.COSINE),
            )

    def _index_vector(self, record: MemoryRecord) -> None:
        if record.id is None:
            return
        self.qdrant.upsert(
            collection_name=self.settings.qdrant_collection,
            points=[
                PointStruct(
                    id=record.id,
                    vector=self._embed(record.content),
                    payload={
                        "memory_type": record.memory_type.value,
                        "source_agent": record.source_agent.value,
                        "title": record.title,
                    },
                )
            ],
        )

    def _embed(self, text: str) -> list[float]:
        buckets = [0.0] * 32
        for token in re.findall(r"\w+", text.lower()):
            buckets[hash(token) % len(buckets)] += 1.0
        norm = sum(value * value for value in buckets) ** 0.5 or 1.0
        return [value / norm for value in buckets]

    def _extract_entities(self, text: str) -> list[Entity]:
        candidates = re.findall(r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3}\b", text)
        unique = []
        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)
        return [Entity(name=item, type="concept", salience=0.6) for item in unique[:20]]

    def _extract_relations(self, text: str, entities: list[Entity]) -> list[Relation]:
        if len(entities) < 2:
            return []
        first = entities[0].name
        return [
            Relation(source=first, target=entity.name, type="co_occurs_with", evidence=text[:240])
            for entity in entities[1:8]
        ]

    def _from_orm(self, row: MemoryORM) -> MemoryRecord:
        return MemoryRecord(
            id=row.id,
            memory_type=MemoryType(row.memory_type),
            source_agent=AgentRole(row.source_agent),
            title=row.title,
            content=row.content,
            entities=[Entity(**entity) for entity in row.entities],
            relations=[Relation(**relation) for relation in row.relations],
            metadata=row.metadata_,
            created_at=row.created_at,
        )


class RemoteGBrainProxy(LocalGBrain):
    def enrich(self, record: MemoryRecord) -> MemoryRecord:
        if not self.settings.gbrain_base_url:
            return super().enrich(record)
        headers = {"Authorization": f"Bearer {self.settings.gbrain_api_key}"} if self.settings.gbrain_api_key else {}
        with httpx.Client(timeout=15) as client:
            response = client.post(
                f"{self.settings.gbrain_base_url.rstrip('/')}/memories/enrich",
                json=record.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            return MemoryRecord.model_validate(response.json())
