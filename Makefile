.PHONY: up down test check seed
up:
	docker compose up --build -d --wait
down:
	docker compose down
test:
	docker compose exec backend pytest
check:
	docker compose exec backend python manage.py check
	docker compose exec backend python manage.py makemigrations --check --dry-run
	docker compose exec backend ruff check .
	docker compose exec backend ruff format --check .
seed:
	docker compose exec backend python manage.py seed_demo
