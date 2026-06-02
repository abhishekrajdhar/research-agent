from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(StrEnum):
    research_scientist = "research_scientist"
    ml_engineer = "ml_engineer"
    planner = "planner"
    critic = "critic"
    memory = "memory"


class MemoryType(StrEnum):
    episodic = "episodic"
    semantic = "semantic"
    procedural = "procedural"
    reflection = "reflection"


class TaskStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class ResearchRequest(BaseModel):
    question: str = Field(min_length=8)
    constraints: dict[str, Any] = Field(default_factory=dict)
    target_outputs: list[str] = Field(default_factory=lambda: ["paper_draft", "experiment_plan"])


class AgentMessage(BaseModel):
    role: AgentRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent: AgentRole
    summary: str
    findings: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class Entity(BaseModel):
    name: str
    type: str
    salience: float = Field(default=0.5, ge=0.0, le=1.0)


class Relation(BaseModel):
    source: str
    target: str
    type: str
    evidence: str


class MemoryRecord(BaseModel):
    id: str | None = None
    memory_type: MemoryType
    source_agent: AgentRole
    title: str
    content: str
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ResearchPipelineResult(BaseModel):
    task_id: str
    question: str
    literature_review: AgentResult
    gap_analysis: AgentResult
    hypothesis: AgentResult
    experiment_design: AgentResult
    experiment_execution: AgentResult
    evaluation: AgentResult
    paper_draft: AgentResult
    review: AgentResult
    memory_update: AgentResult
    reflection_id: str
