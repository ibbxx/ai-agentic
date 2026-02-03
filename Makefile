.PHONY: dev migrate clean

dev:
	docker-compose up --build

migrate:
	alembic upgrade head

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
