# Autonomous Multi-Agent Research Lab Architecture

## Decision Summary

| Choice | Options Compared | Decision | Rationale |
| --- | --- | --- | --- |
| Agent runtime | Single monolith, queue workers, provider adapters | FastAPI orchestrator with Hermes and Gemini adapters | Runs locally now and can delegate reasoning to Hermes or Gemini when credentials are configured. |
| Memory | Vector-only, graph-only, hybrid | GBrain-style hybrid graph plus Qdrant vector index | Supports semantic retrieval, entity relationships, timelines, and durable audit records. |
| Persistence | Files, SQLite, PostgreSQL | PostgreSQL | Production-ready JSONB, indexing, relational task/experiment audit trail. |
| Coordination | Fully autonomous infinite loop, explicit pipeline | Explicit research pipeline with reflection loop | Safer, auditable, and easier to test while still self-improving after every task. |

## Agent Organization

```mermaid
flowchart LR
    UI[Streamlit Frontend] --> API[FastAPI API]
    API --> Planner[Planner Agent]
    Planner --> Scientist[Research Scientist]
    Scientist --> MLE[ML Engineer]
    MLE --> Critic[Critic Agent]
    Critic --> Memory[Memory Agent]
    Memory --> Reflection[Reflection Engine]
    Reflection --> GBrain[GBrain Memory Layer]
    Scientist <--> GBrain
    MLE <--> GBrain
    Planner <--> GBrain
    Critic <--> GBrain
    Memory <--> GBrain
```

## Research Pipeline

```mermaid
flowchart TD
    A[Research Question] --> B[Literature Search]
    B --> C[Gap Analysis]
    C --> D[Hypothesis Generation]
    D --> E[Experiment Design]
    E --> F[Experiment Execution]
    F --> G[Evaluation]
    G --> H[Paper Draft]
    H --> I[Review]
    I --> J[Memory Update]
    J --> K[Reflection Record]
```

## Memory Architecture

```mermaid
flowchart TB
    subgraph GBrain
      E[Episodic Memory]
      S[Semantic Memory]
      P[Procedural Memory]
      R[Reflection Memory]
      KG[Knowledge Graph]
      T[Timeline]
      V[Qdrant Semantic Index]
    end
    E --> KG
    S --> KG
    P --> KG
    R --> KG
    KG --> T
    KG --> V
    V --> Retrieval[Agent Retrieval]
```

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Agent and persistence health snapshot. |
| `POST` | `/research` | Run the full autonomous research pipeline. |
| `GET` | `/tasks` | Inspect recent task state. |
| `GET` | `/memory` | Inspect recent GBrain memory records. |
| `GET` | `/metrics` | Prometheus metrics. |

## Frontend

The Streamlit frontend is a thin operational client over the FastAPI service. It provides:

- Research run submission.
- Pipeline output review.
- Task table.
- Memory browser.
- Health and Prometheus metrics view.

## Database Schema

The SQL schema is in `infra/postgres/001_schema.sql` and includes:

- `tasks`: pipeline state and final results.
- `memories`: episodic, semantic, procedural, and reflection records with graph entities and relations.
- `reflections`: lessons learned, mistakes, and improvement opportunities after each completed task.
- `experiments`: metrics and artifacts for experiment execution.

## Operations

1. Copy `.env.example` to `.env`.
2. For local `uvicorn`, keep `DATABASE_URL`, `REDIS_URL`, and `QDRANT_URL` on `localhost`.
3. To use Gemini instead, set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, and optional `GEMINI_MODEL`.
4. Configure `HERMES_API_KEY` and optional `GBRAIN_BASE_URL` when available.
5. Run `./scripts/deploy.sh`; Docker Compose overrides database, Redis, and Qdrant URLs to internal service names.
6. Open `http://localhost:8000/docs`.
7. Open the Streamlit frontend at `http://localhost:8501`.
8. Monitor Prometheus at `http://localhost:9090`.
