from typing import Any

from sqlalchemy.orm import Session

from app.agents import (
    CriticAgent,
    MemoryAgent,
    MLEngineerAgent,
    PlannerAgent,
    ResearchScientistAgent,
)
from app.agents.hermes import HermesClient, LLMClient
from app.db.models import ExperimentORM, TaskORM
from app.memory.service import MemoryService
from app.orchestration.reflection import ReflectionEngine
from app.research.schemas import AgentResult, ResearchPipelineResult, ResearchRequest


class ResearchPipeline:
    def __init__(self, session: Session, llm: LLMClient | None = None) -> None:
        self.session = session
        self.memory = MemoryService(session)
        self.llm = llm or HermesClient()
        self.planner = PlannerAgent(self.llm, self.memory)
        self.scientist = ResearchScientistAgent(self.llm, self.memory)
        self.engineer = MLEngineerAgent(self.llm, self.memory)
        self.critic = CriticAgent(self.llm, self.memory)
        self.memory_agent = MemoryAgent(self.llm, self.memory)
        self.reflection = ReflectionEngine(session, self.memory)

    def run(self, request: ResearchRequest) -> ResearchPipelineResult:
        task = TaskORM(title=request.question, status="running", payload=request.model_dump())
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        try:
            context: dict[str, Any] = {"request": request.model_dump(), "task_id": task.id}
            plan = self.planner.run("Decompose the research question into a roadmap.", context)
            context["plan"] = plan.model_dump()

            literature = self.scientist.run("Perform literature search and benchmark analysis.", context)
            context["literature"] = literature.model_dump()

            gap = self.scientist.run("Analyze research gaps and unresolved assumptions.", context)
            context["gap_analysis"] = gap.model_dump()

            hypothesis = self.scientist.run("Generate a falsifiable hypothesis and novelty claim.", context)
            context["hypothesis"] = hypothesis.model_dump()

            experiment_design = self.engineer.run("Design a reproducible experiment.", context)
            context["experiment_design"] = experiment_design.model_dump()

            experiment_execution = self.engineer.run("Execute or simulate experiment workflow.", context)
            self._record_experiment(task.id, experiment_execution)
            context["experiment_execution"] = experiment_execution.model_dump()

            evaluation = self.critic.run("Evaluate results, citations, hallucination risk, and novelty.", context)
            context["evaluation"] = evaluation.model_dump()

            paper_draft = self.scientist.run("Draft a paper outline with claims, methods, and limitations.", context)
            context["paper_draft"] = paper_draft.model_dump()

            review = self.critic.run("Review the paper draft and challenge weak claims.", context)
            context["review"] = review.model_dump()

            memory_update = self.memory_agent.run("Consolidate pipeline memories and timeline.", context)
            results = [
                plan,
                literature,
                gap,
                hypothesis,
                experiment_design,
                experiment_execution,
                evaluation,
                paper_draft,
                review,
                memory_update,
            ]
            reflection_id = self.reflection.reflect(task.id, results)
            task.status = "completed"
            task.result = {"reflection_id": reflection_id}
            self.session.commit()
            return ResearchPipelineResult(
                task_id=task.id,
                question=request.question,
                literature_review=literature,
                gap_analysis=gap,
                hypothesis=hypothesis,
                experiment_design=experiment_design,
                experiment_execution=experiment_execution,
                evaluation=evaluation,
                paper_draft=paper_draft,
                review=review,
                memory_update=memory_update,
                reflection_id=reflection_id,
            )
        except Exception:
            task.status = "failed"
            self.session.commit()
            raise

    def _record_experiment(self, task_id: str, result: AgentResult) -> None:
        experiment = ExperimentORM(
            task_id=task_id,
            name=f"Experiment for {task_id}",
            status="completed",
            metrics={"confidence": result.confidence},
            artifacts=result.artifacts,
        )
        self.session.add(experiment)
        self.session.commit()
