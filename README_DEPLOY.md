Render deployment guide
=======================

This file contains step-by-step instructions to deploy the full stack (API + frontend + managed Postgres) to Render.

Prerequisites
- A Render account (https://render.com)
- GitHub repo with this project

High-level steps
1. Backend (FastAPI)
   - Create a new Web Service on Render, select Docker, connect to the GitHub repo and choose the root Dockerfile.
   - Set the start command to: `uvicorn main:app --host 0.0.0.0 --port 8000` if not autodetected.
   - Add environment variables (see below).
   - Deploy.

2. Managed Postgres
   - In Render, create a Managed Postgres instance.
   - Copy the DATABASE_URL value into the backend service environment.

3. Frontend (Streamlit)
   - Create a second Web Service on Render using `Dockerfile.frontend`.
   - Set environment variable `API_BASE_URL` to your backend's public URL.
   - Deploy.

Required environment variables
- DATABASE_URL: postgresql+psycopg://user:pass@host:5432/dbname
- REDIS_URL: redis://... (optional, only if you're using Redis)
- QDRANT_URL: http://... (optional; use Qdrant Cloud if you want vector search)
- QDRANT_COLLECTION: research_memories
- GEMINI_API_KEY: (optional; set to use Gemini as primary provider)
- HERMES_API_KEY: (optional)
- LLM_PROVIDER: hermes|gemini (default: hermes)
- LLM_MODEL: hermes-default (or gemini model id)

One-off DB initialization
- Either run the `scripts/create_tables.py` locally (with DATABASE_URL pointing to your Render Postgres) or create a one-off job in Render to run it.

Notes
- If you prefer a cheaper/simple option and can tolerate no Qdrant/Redis, switch to LocalGBrain (SQL fallback) by leaving QDRANT_URL unset and using the default settings.
- Keep API keys secret: configure them in Render's dashboard, do not commit keys to git.
