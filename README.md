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
