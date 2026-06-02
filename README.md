# Autonomous Multi-Agent Research Lab

A production-oriented scaffold for a self-improving AI research organization using Hermes Agent as the reasoning adapter and a GBrain-style hybrid memory system backed by PostgreSQL and Qdrant.

## Capabilities

- Five specialist agents: Research Scientist, ML Engineer, Planner, Critic, and Memory Agent.
- Full research pipeline from question to literature review, gap analysis, hypothesis, experiment plan, execution scaffold, evaluation, paper draft, review, memory update, and reflection.
- Episodic, semantic, procedural, and reflection memory.
- Knowledge graph entity and relationship extraction.
- Prometheus metrics, health checks, task tracking, experiment tracking, and error accounting.
- Docker Compose deployment with FastAPI, PostgreSQL, Redis, Qdrant, and Prometheus.

## Run Locally

```bash
cp .env.example .env
./scripts/deploy.sh
```

Open `http://localhost:8000/docs`.

## Example Request

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"question":"How can graph memory improve hallucination detection in multi-agent research systems?"}'
```

## Hermes and GBrain

The app runs without credentials through deterministic offline adapters. Set `HERMES_API_KEY` to route generation through a Hermes-compatible chat completions endpoint. Set `GBRAIN_BASE_URL` to delegate memory enrichment to an external GBrain service while retaining local durable storage.

## Documentation

See `docs/architecture.md` for diagrams, tradeoffs, schema summary, memory design, and endpoint descriptions.
