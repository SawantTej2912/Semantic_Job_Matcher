
.PHONY: build up down logs help

help:
	@echo "Available commands:"
	@echo "  make build    - Build all docker containers"
	@echo "  make up       - Start all services with docker compose"
	@echo "  make down     - Stop and remove all containers"
	@echo "  make logs     - View logs from all services"

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f
