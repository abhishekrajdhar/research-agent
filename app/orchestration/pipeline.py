from typing import Any
from typing import Optional
import traceback

from sqlalchemy.orm import Session

from app.agents import (
    CriticAgent,
    MemoryAgent,
    MLEngineerAgent,
    PlannerAgent,
    ResearchScientistAgent,
)
from app.agents.hermes import LLMClient, create_llm_client
from app.db.models import ExperimentORM, TaskORM
from app.memory.service import MemoryService
from app.orchestration.reflection import ReflectionEngine
from app.research.schemas import AgentResult, ResearchPipelineResult, ResearchRequest


class ResearchPipeline:
    def __init__(self, session: Session, llm: LLMClient | None = None) -> None:
        self.session = session
        self.memory = MemoryService(session)
        self.llm = llm or create_llm_client()
        self.planner = PlannerAgent(self.llm, self.memory)
        self.scientist = ResearchScientistAgent(self.llm, self.memory)
        self.engineer = MLEngineerAgent(self.llm, self.memory)
        self.critic = CriticAgent(self.llm, self.memory)
        self.memory_agent = MemoryAgent(self.llm, self.memory)
        self.reflection = ReflectionEngine(session, self.memory)
    def _update_task_result(self, task_id: str, stage_key: str, result: AgentResult) -> None:
        task = self.session.get(TaskORM, task_id)
        if task is None:
            return
        existing = task.result or {}
        existing[stage_key] = result.model_dump()
        task.result = existing
        # keep status running while updating
        task.status = "running"
        self.session.add(task)
        self.session.commit()

    def run(self, request: ResearchRequest, existing_task_id: Optional[str] = None) -> ResearchPipelineResult:
        # If an existing task id is provided, use it and mark running. Otherwise create a new task.
        if existing_task_id:
            task = self.session.get(TaskORM, existing_task_id)
            if task is None:
                task = TaskORM(title=request.question, status="running", payload=request.model_dump())
                self.session.add(task)
                self.session.commit()
                self.session.refresh(task)
            else:
                task.status = "running"
                task.payload = request.model_dump()
                self.session.add(task)
                self.session.commit()
                self.session.refresh(task)
        else:
            task = TaskORM(title=request.question, status="running", payload=request.model_dump())
            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)

        try:
            context: dict[str, Any] = {"request": request.model_dump(), "task_id": task.id}

            plan = self.planner.run("Decompose the research question into a roadmap.", context)
            self._update_task_result(task.id, "plan", plan)
            context["plan"] = plan.model_dump()

            literature = self.scientist.run("Perform literature search and benchmark analysis.", context)
            self._update_task_result(task.id, "literature_review", literature)
            context["literature"] = literature.model_dump()

            gap = self.scientist.run("Analyze research gaps and unresolved assumptions.", context)
            self._update_task_result(task.id, "gap_analysis", gap)
            context["gap_analysis"] = gap.model_dump()

            hypothesis = self.scientist.run("Generate a falsifiable hypothesis and novelty claim.", context)
            self._update_task_result(task.id, "hypothesis", hypothesis)
            context["hypothesis"] = hypothesis.model_dump()

            experiment_design = self.engineer.run("Design a reproducible experiment.", context)
            self._update_task_result(task.id, "experiment_design", experiment_design)
            context["experiment_design"] = experiment_design.model_dump()

            experiment_execution = self.engineer.run("Execute or simulate experiment workflow.", context)
            self._record_experiment(task.id, experiment_execution)
            self._update_task_result(task.id, "experiment_execution", experiment_execution)
            context["experiment_execution"] = experiment_execution.model_dump()

            evaluation = self.critic.run("Evaluate results, citations, hallucination risk, and novelty.", context)
            self._update_task_result(task.id, "evaluation", evaluation)
            context["evaluation"] = evaluation.model_dump()

            paper_draft = self.scientist.run("Draft a paper outline with claims, methods, and limitations.", context)
            self._update_task_result(task.id, "paper_draft", paper_draft)
            context["paper_draft"] = paper_draft.model_dump()

            review = self.critic.run("Review the paper draft and challenge weak claims.", context)
            self._update_task_result(task.id, "review", review)
            context["review"] = review.model_dump()

            memory_update = self.memory_agent.run("Consolidate pipeline memories and timeline.", context)
            self._update_task_result(task.id, "memory_update", memory_update)
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

            # final task update
            task.status = "completed"
            existing = task.result or {}
            existing["reflection_id"] = reflection_id
            task.result = existing
            self.session.add(task)
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
        except Exception as e:
            # capture exception details into the task result for visibility in the UI
            self.session.rollback()
            failed_task = self.session.get(TaskORM, task.id)
            tb = traceback.format_exc()
            if failed_task is not None:
                failed_task.status = "failed"
                existing = failed_task.result or {}
                existing["error"] = str(e)
                existing["traceback"] = tb
                failed_task.result = existing
                self.session.add(failed_task)
                self.session.commit()
            # re-raise so callers still see the exception in logs
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
