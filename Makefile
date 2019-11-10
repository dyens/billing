.PHONY: flake mypy pytest check deps stop-deps

flake:
	-poetry run flake8 || true

mypy:
	-poetry run mypy billing || true

pytest:
	-poetry run pytest || true

check: flake mypy pytest

deps:
	-docker run -d \
      --name billing_postgres \
      -e POSTGRES_PASSWORD=pgpass \
      -e POSTGRES_USER=pguser \
      -e POSTGRES_DB=pgdb \
      -p 5436:5432 \
      postgres \
  || docker start billing_postgres


test-deps:
	-docker run -d \
      --name billing_test_postgres \
      -v billing_test_postgres_volume:/var/lib/postgresql/data \
      -e POSTGRES_PASSWORD=pgpass \
      -e POSTGRES_USER=pguser \
      -e POSTGRES_DB=pgdb \
      -p 5437:5432 \
      postgres \
  || docker start billing_test_postgres

psql:
	-psql -U pguser -h 127.0.0.1 -p 5436 -d pgdb


stop-deps:
	-docker stop billing_postgres

stop-test-deps:
	-docker stop billing_test_postgres
