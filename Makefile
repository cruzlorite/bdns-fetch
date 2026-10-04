# Makefile for bdns.

.PHONY: help install test test-sync test-integration lint format check-docs docs clean all

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "BDNS - Available Make Targets:"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install the package, its extras and the development tools
	uv sync --all-extras

test: ## Run the unit tests (no network)
	uv run pytest

test-sync: ## Run bdns.sync's tests only (BDNS_SYNC_TEST_URL picks the database)
	uv run pytest tests/sync

test-integration: ## Run the live tests against the real BDNS API
	uv run pytest -m integration --no-cov

lint: ## Lint and check formatting with ruff
	uv run ruff check .
	uv run ruff format --check .

format: ## Format code with ruff
	uv run ruff format .

check-docs: ## Verify doc references, docstring conventions and the site build
	uv run python scripts/check_doc_refs.py
	uv run python scripts/check_docstrings.py
	uv run mkdocs build --strict
	uv run python scripts/check_site_links.py

docs: ## Serve the documentation site locally
	uv run mkdocs serve

clean: ## Remove build artifacts and cache files
	rm -rf dist/ build/ site/ htmlcov/ .pytest_cache/ .ruff_cache/ .coverage
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} +

all: install lint check-docs test ## Install, lint, check docs and test everything
