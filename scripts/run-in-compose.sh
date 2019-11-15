#! /bin/sh

./scripts/wait-for-it.sh billing_db:5432 -- poetry run alembic upgrade head
poetry run python main.py
