#!/bin/bash
# Local dev server. Uses a local SQLite file (buty-tinder/shoes.db) when
# DATABASE_URL is not set, so you can test without any database.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install -q -r requirements.txt
fi

PORT="${PORT:-8080}"
exec ./.venv/bin/python -m flask --app app run --port "$PORT" --debug
