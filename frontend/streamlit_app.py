import os
from typing import Any

import httpx
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def request_json(method: str, path: str, **kwargs: Any) -> Any:
    with httpx.Client(timeout=120) as client:
        response = client.request(method, f"{API_BASE_URL}{path}", **kwargs)
        response.raise_for_status()
        return response.json()


def request_text(method: str, path: str, **kwargs: Any) -> str:
    with httpx.Client(timeout=30) as client:
        response = client.request(method, f"{API_BASE_URL}{path}", **kwargs)
        response.raise_for_status()
        return response.text


def render_status() -> None:
    try:
        health = request_json("GET", "/health")
    except httpx.HTTPError as exc:
        st.error(f"API unavailable: {exc}")
        return

    cols = st.columns(3)
    cols[0].metric("Status", str(health.get("status", "unknown")).upper())
    cols[1].metric("Tasks", health.get("tasks", 0))
    cols[2].metric("Memories", health.get("memories", 0))


def render_research_form() -> None:
    st.subheader("Research Run")
    question = st.text_area(
        "Research question",
        value="How can graph memory improve hallucination detection in multi-agent research systems?",
        height=110,
    )
    target_outputs = st.multiselect(
        "Target outputs",
        ["paper_draft", "experiment_plan", "benchmark_analysis", "memory_report"],
        default=["paper_draft", "experiment_plan"],
    )
    with st.expander("Constraints"):
        max_runtime = st.number_input("Max runtime minutes", min_value=1, max_value=240, value=30)
        require_citations = st.checkbox("Require citation verification", value=True)
        reproducibility = st.checkbox("Prioritize reproducibility", value=True)

    if not st.button("Run Research", type="primary"):
        return

    payload = {
        "question": question.strip(),
        "target_outputs": target_outputs,
        "constraints": {
            "max_runtime_minutes": max_runtime,
            "require_citation_verification": require_citations,
            "prioritize_reproducibility": reproducibility,
        },
    }
    if len(payload["question"]) < 8:
        st.warning("Use a more specific research question.")
        return

    with st.spinner("Queuing multi-agent pipeline..."):
        try:
            resp = request_json("POST", "/research", json=payload)
        except httpx.HTTPStatusError as exc:
            st.error(f"Research run failed: HTTP {exc.response.status_code}")
            st.code(exc.response.text)
            return
        except httpx.HTTPError as exc:
            st.error(f"Research run failed: {exc}")
            return

    task_id = resp.get("task_id")
    if not task_id:
        st.error("No task id returned from API")
        return

    st.info(f"Task queued: {task_id}")

    # poll for incremental results
    placeholder = st.empty()
    finished = False
    with placeholder.container():
        while not finished:
            try:
                status = request_json("GET", f"/tasks/{task_id}")
            except Exception as exc:
                st.error(f"Could not fetch task status: {exc}")
                return

            st.write(f"Task {task_id} — status: {status.get('status')}")
            result = status.get("result", {})
            if status.get("status") in {"completed", "failed"}:
                finished = True
            # render whatever partial results we have
            render_pipeline_result_partial(result)
            if not finished:
                st.sleep(1)

    if status.get("status") == "completed":
        st.success(f"Completed task {task_id}")
    else:
        st.error(f"Task {task_id} finished with status: {status.get('status')}")


def render_pipeline_result_partial(result: dict[str, Any]) -> None:
    st.subheader("Pipeline (partial)")
    stages = [
        ("Plan", "plan"),
        ("Literature", "literature_review"),
        ("Gap Analysis", "gap_analysis"),
        ("Hypothesis", "hypothesis"),
        ("Experiment Design", "experiment_design"),
        ("Experiment Execution", "experiment_execution"),
        ("Evaluation", "evaluation"),
        ("Paper Draft", "paper_draft"),
        ("Review", "review"),
        ("Memory Update", "memory_update"),
    ]
    for label, key in stages:
        stage = result.get(key)
        if not stage:
            st.caption(f"{label}: (pending)")
            continue
        with st.expander(label, expanded=False):
            st.write(stage.get("summary", "No summary"))
            st.progress(float(stage.get("confidence", 0.0)))
            findings = stage.get("findings", [])
            if findings:
                st.markdown("**Findings**")
                for finding in findings:
                    st.write(f"- {finding}")


def render_pipeline_result(result: dict[str, Any]) -> None:
    st.subheader("Pipeline Output")
    st.caption(f"Reflection: {result.get('reflection_id', 'not recorded')}")
    stages = [
        ("Literature", "literature_review"),
        ("Gap Analysis", "gap_analysis"),
        ("Hypothesis", "hypothesis"),
        ("Experiment Design", "experiment_design"),
        ("Experiment Execution", "experiment_execution"),
        ("Evaluation", "evaluation"),
        ("Paper Draft", "paper_draft"),
        ("Review", "review"),
        ("Memory Update", "memory_update"),
    ]
    for label, key in stages:
        stage = result.get(key, {})
        with st.expander(label, expanded=label in {"Evaluation", "Memory Update"}):
            st.write(stage.get("summary", "No summary"))
            st.progress(float(stage.get("confidence", 0.0)))
            findings = stage.get("findings", [])
            if findings:
                st.markdown("**Findings**")
                for finding in findings:
                    st.write(f"- {finding}")
            artifacts = stage.get("artifacts", {})
            if artifacts:
                st.markdown("**Artifacts**")
                st.json(artifacts)


def render_tasks() -> None:
    st.subheader("Tasks")
    try:
        tasks = request_json("GET", "/tasks")
    except httpx.HTTPError as exc:
        st.error(f"Could not load tasks: {exc}")
        return
    if not tasks:
        st.info("No tasks yet.")
        return
    st.dataframe(tasks, use_container_width=True, hide_index=True)


def render_memory() -> None:
    st.subheader("Memory")
    limit = st.slider("Records", min_value=10, max_value=100, value=50, step=10)
    try:
        memories = request_json("GET", f"/memory?limit={limit}")
    except httpx.HTTPError as exc:
        st.error(f"Could not load memory: {exc}")
        return
    if not memories:
        st.info("No memory records yet.")
        return

    memory_types = sorted({item["memory_type"] for item in memories})
    selected_types = st.multiselect("Memory type", memory_types, default=memory_types)
    filtered = [item for item in memories if item["memory_type"] in selected_types]
    for item in filtered:
        with st.expander(f"{item['memory_type']} | {item['title']}"):
            st.caption(f"{item['source_agent']} | {item.get('created_at', '')}")
            st.write(item["content"])
            cols = st.columns(2)
            cols[0].json(item.get("entities", []))
            cols[1].json(item.get("relations", []))


def render_monitoring() -> None:
    st.subheader("Monitoring")
    render_status()
    try:
        metrics = request_text("GET", "/metrics")
    except httpx.HTTPError as exc:
        st.error(f"Could not load metrics: {exc}")
        return
    st.code(metrics, language="text")


def main() -> None:
    st.set_page_config(
        page_title="Research Lab",
        page_icon="RL",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Autonomous Research Lab")
    with st.sidebar:
        st.caption("API")
        st.code(API_BASE_URL, language="text")
        render_status()

    tabs = st.tabs(["Run", "Tasks", "Memory", "Monitoring"])
    with tabs[0]:
        render_research_form()
    with tabs[1]:
        render_tasks()
    with tabs[2]:
        render_memory()
    with tabs[3]:
        render_monitoring()


if __name__ == "__main__":
    main()
