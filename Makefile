# Makefile for BDNS Fetch project

.PHONY: help install dev-install test test-integration test-working lint format clean all

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "BDNS Fetch - Available Make Targets:"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	poetry install --no-dev

dev-install: ## Install project with development dependencies
	poetry install

test-cli: ## Run CLI tests
	@echo "🚀 Running CLI Tests..."
	poetry run python -m pytest tests/test_cli.py -v -s
	@echo "🎉 CLI Tests Completed!"

test-integration: ## Run integration tests against real BDNS API
	@echo "🚀 Running Integration Tests Against Real BDNS API..."
	poetry run python -m pytest tests/integration/ -v -s
	@echo "🎉 Integration Tests Completed!"

test: ## Run all tests (CLI + integration)
	@echo "🚀 Running All Tests..."
	poetry run python -m pytest tests/ -v
	@echo "🎉 All Tests Completed!"

lint: ## Run code linting with ruff
	poetry run ruff check .

format: ## Format code with ruff formatter
	poetry run ruff format .

clean: ## Remove build artifacts and cache files
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: dev-install lint format test ## Install, lint, format, and test everything
