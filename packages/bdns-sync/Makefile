# Makefile for BDNS Sync project

.PHONY: help install dev-install test lint format check-docs clean all

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "BDNS Sync - Available Make Targets:"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	poetry install --only main

dev-install: ## Install project with development dependencies
	poetry install

test: ## Run all tests
	poetry run python -m pytest tests/ -v

lint: ## Run code linting with ruff
	poetry run ruff check .

format: ## Format code with ruff formatter
	poetry run ruff format .

check-docs: ## Verify doc references and docstring conventions
	poetry run python scripts/check_doc_refs.py
	poetry run python scripts/check_docstrings.py

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

all: dev-install lint format check-docs test ## Install, lint, format, check docs, and test everything
