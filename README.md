# Autonomous Multi-Agent Research Lab

A lightweight production scaffold for an autonomous research pipeline. It includes:

- Five specialist agents: Planner, Research Scientist, ML Engineer, Critic, Memory Agent.
- A sequential research pipeline (plan → literature → gaps → hypothesis → experiment → evaluation → draft → review → memory → reflection).
- Durable storage in PostgreSQL, an optional Qdrant vector index for semantic search, and a simple local GBrain fallback.
- Streamlit frontend, FastAPI backend, Prometheus metrics, and Docker Compose for local development.

This repository is intended as a deployable starting point. 

Quick start (Docker Compose)

1. Copy environment template and edit values you need:

```bash
cp .env.example .env
# edit .env if needed (DB creds, API keys, etc.)
```

2. Build and start the stack:

```bash
./scripts/deploy.sh
```

3. Open the services in your browser:

- API docs: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501
- Prometheus: http://localhost:9090

Run a sample research job

```bash
curl -sS -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"question":"How can graph memory improve hallucination detection in multi-agent research systems?"}'
```

Development notes

- If you run services directly (e.g., `uvicorn main:app`), ensure `DATABASE_URL` points to a reachable Postgres instance. The default in `.env.example` is a local DB; Docker Compose overrides service names when using containers.
- To create the DB schema, run the helper script from the project root:

```bash
python3 scripts/create_tables.py
```

LLM providers and fallback behavior

- The app supports two adapters: Gemini (Google) and Hermes (local/managed). The server-side LLM wrapper now tries Gemini first with retries and then falls back to Hermes on transient errors.
- Provide credentials via env vars (do not commit keys):

```bash
# Prefer Gemini (recommended if you have credentials and quota)
GEMINI_API_KEY=...          # set on the server/provider
GEMINI_MODEL=gemini-2.5-flash
LLM_PROVIDER=gemini

# Or use Hermes (local/demo)
HERMES_API_KEY=...          # optional
LLM_PROVIDER=hermes
```

UX: per-stage provider metadata

Each stage result records which provider answered that stage (stage.artifacts.provider). The Streamlit UI surfaces stage status and you can inspect provider attribution in the task details.

Deploying to Render

See `README_DEPLOY.md` for a step-by-step Render deployment guide and an example `render/render.yaml` manifest.

More documentation

See `docs/architecture.md` for architecture diagrams, API endpoint list, the DB schema location, and operational notes.
# Autonomous Multi-Agent Research Lab

A production-oriented scaffold for a self-improving AI research organization using Hermes Agent as the reasoning adapter and a GBrain-style hybrid memory system backed by PostgreSQL and Qdrant.

## Capabilities

- Five specialist agents: Research Scientist, ML Engineer, Planner, Critic, and Memory Agent.
- Full research pipeline from question to literature review, gap analysis, hypothesis, experiment plan, execution scaffold, evaluation, paper draft, review, memory update, and reflection.
- Episodic, semantic, procedural, and reflection memory.
- Knowledge graph entity and relationship extraction.
- Prometheus metrics, health checks, task tracking, experiment tracking, and error accounting.
- Docker Compose deployment with FastAPI, Streamlit, PostgreSQL, Redis, Qdrant, and Prometheus.

## Run Locally

For Docker Compose:

```bash
cp .env.example .env
./scripts/deploy.sh
```

Open `http://localhost:8000/docs`.

Open the Streamlit frontend at `http://localhost:8501`.

For direct `uvicorn` development, make sure PostgreSQL is reachable at the `DATABASE_URL` in `.env`. The default `.env.example` uses `localhost`; Docker Compose overrides that to service names internally.

## Example Request

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"question":"How can graph memory improve hallucination detection in multi-agent research systems?"}'
```

## LLM Providers and GBrain

The app runs without credentials through deterministic offline adapters.

Use Hermes:

```env
LLM_PROVIDER=hermes
HERMES_API_KEY=...
LLM_MODEL=hermes-default
```

Use Gemini:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

Gemini is called server-side through the official `generateContent` REST API using the `x-goog-api-key` header. Set `GBRAIN_BASE_URL` to delegate memory enrichment to an external GBrain service while retaining local durable storage.

## Documentation

See `docs/architecture.md` for diagrams, tradeoffs, schema summary, memory design, and endpoint descriptions.
