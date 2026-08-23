.PHONY: help setup run test lint format docker-build docker-up clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies and setup environment
	python -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -e ".[dev]"
	@[ -f .env ] || cp .env.example .env

run: ## Start development server
	python -m src.main

test: ## Run unit and integration tests with coverage
	pytest tests/ -v --tb=short

lint: ## Run code linter
	ruff check src/ tests/

format: ## Auto-format code
	ruff format src/ tests/

docker-build: ## Build docker image
	docker build -t ai-email-automation-agent .

docker-up: ## Start container via docker-compose
	docker-compose up -d

clean: ## Clean build artifacts and test caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
