import os
from typing import Any

import httpx
import streamlit as st
import time


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
    max_polls = 60 * 10  # 10 minutes max by default
    poll_interval = 1.0
    consecutive_errors = 0
    max_consecutive_errors = 5
    start_ts = time.time()

    with placeholder.container():
        poll_count = 0
        # create single placeholders for status and elapsed so we update in-place
        status_ph = st.empty()
        elapsed_ph = st.empty()
        progress_ph = st.progress(0)
        while not finished and poll_count < max_polls:
            try:
                status = request_json("GET", f"/tasks/{task_id}")
                consecutive_errors = 0
            except Exception as exc:
                consecutive_errors += 1
                status_ph.warning(f"Could not fetch task status (attempt {consecutive_errors}): {exc}")
                if consecutive_errors >= max_consecutive_errors:
                    status_ph.error("Too many consecutive errors fetching task status — aborting.")
                    return
                time.sleep(min(5, poll_interval * consecutive_errors))
                poll_count += 1
                continue

            poll_count += 1
            elapsed = int(time.time() - start_ts)
            # update placeholders in-place
            elapsed_ph.text(f"Elapsed: {elapsed}s")
            result = status.get("result", {}) or {}

            # show concise agent-level progress while pipeline is running
            current_worker = _current_stage_from_result(result)
            if current_worker and status.get("status") not in {"completed", "failed"}:
                status_ph.info(f"{current_worker} is working...")
            else:
                status_ph.info(f"Task {task_id} — status: {status.get('status')}")
                # render whatever partial results we have (for visibility)
                render_pipeline_result_partial(result)

            if status.get("status") in {"completed", "failed"}:
                finished = True
                break

            # show a lightweight progress indicator for the polling duration
            try:
                # scale progress to max_polls
                prog = min(1.0, poll_count / max_polls)
                progress_ph.progress(int(prog * 100))
            except Exception:
                pass

            time.sleep(poll_interval)

            if not finished:
                status_ph.error("Polling timed out before the pipeline completed. Check the Tasks tab for details.")
        else:
            # show final output only once finished
            if status.get("status") == "completed":
                final_result = status.get("result", {}) or {}
                render_pipeline_result(final_result)

    if status.get("status") == "completed":
        st.success(f"Completed task {task_id}")
    else:
        st.error(f"Task {task_id} finished with status: {status.get('status')}")


def render_pipeline_result_partial(result: dict[str, Any]) -> None:
    st.subheader("Pipeline (partial)")
    # surface top-level pipeline errors, if any
    if not result:
        st.caption("No results yet.")
    if result.get("error"):
        st.error(f"Pipeline error: {result.get('error')}")
        tb = result.get("traceback")
        if tb:
            with st.expander("Traceback"):
                # show only the last 2000 characters to avoid huge output
                st.text(tb[-2000:])
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
    # show pipeline-level error if present
    if result.get("error"):
        st.error(f"Pipeline error: {result.get('error')}")
        tb = result.get("traceback")
        if tb:
            with st.expander("Traceback"):
                st.text(tb[-2000:])
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


def _human_stage_name(key: str) -> str:
    mapping = {
        "plan": "Planner",
        "literature_review": "Research Scientist",
        "gap_analysis": "Research Scientist",
        "hypothesis": "Research Scientist",
        "experiment_design": "ML Engineer",
        "experiment_execution": "ML Engineer",
        "evaluation": "Critic",
        "paper_draft": "Research Scientist",
        "review": "Critic",
        "memory_update": "Memory Agent",
    }
    return mapping.get(key, key)


def _current_stage_from_result(result: dict[str, Any]) -> str | None:
    """Return the active worker name based on which stages are present in result.
    If all stages present, return None (meaning pipeline likely completed).
    """
    ordered_keys = [
        "plan",
        "literature_review",
        "gap_analysis",
        "hypothesis",
        "experiment_design",
        "experiment_execution",
        "evaluation",
        "paper_draft",
        "review",
        "memory_update",
    ]
    for key in ordered_keys:
        if key not in result:
            return _human_stage_name(key)
    return None


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
    # present tasks in a select box to view details
    options = [f"{r['title']} — {r['id']} — {r['status']}" for r in tasks]
    choice = st.selectbox("Select a task to view (will wait until it's finished)", options)
    if not choice:
        return
    # extract id from choice
    task_id = choice.split(" — ")[-2] if " — " in choice else None
    if not task_id:
        st.error("Unable to determine task id from selection")
        return

    if st.button("Show final result", key=f"show_{task_id}"):
        # Poll until the task is completed or failed, then render the final result only
        max_polls = 60 * 10
        poll_interval = 1.0
        poll_count = 0
        with st.spinner("Waiting for task to finish..."):
            while poll_count < max_polls:
                try:
                    status = request_json("GET", f"/tasks/{task_id}")
                except Exception as exc:
                    st.warning(f"Error fetching task: {exc}")
                    time.sleep(min(5, poll_interval * (poll_count + 1)))
                    poll_count += 1
                    continue

                if status.get("status") == "completed":
                    final_result = status.get("result", {}) or {}
                    render_pipeline_result(final_result)
                    return
                if status.get("status") == "failed":
                    # show the error info if present
                    res = status.get("result", {}) or {}
                    st.error(f"Task failed: {res.get('error', 'unknown error')}")
                    tb = res.get("traceback")
                    if tb:
                        with st.expander("Traceback"):
                            st.text(tb[-2000:])
                    return

                # still running
                st.info(f"Task {task_id} is {status.get('status')} — waiting...")
                time.sleep(poll_interval)
                poll_count += 1

            st.error("Timed out waiting for task to complete. Check later under Tasks.")


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
