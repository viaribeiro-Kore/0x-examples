#!/usr/bin/env bash
set -euo pipefail
export $(grep -v '^#' .env | xargs -d '\n' -I {} echo {})
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload