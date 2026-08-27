.PHONY: secrets up down migrate seed test bench logs

secrets:
	python scripts/gen_dev_secrets.py

up:
	docker compose up --build -d

down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.seed

test:
	cd backend && python -m pytest -q

bench:
	cd backend && python ../scripts/benchmark.py

logs:
	docker compose logs -f backend
