#!/usr/bin/env bash
set -euo pipefail

curl -fsS http://localhost:8000/health
curl -fsS -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"question":"How can graph memory improve hallucination detection in multi-agent research systems?"}'
