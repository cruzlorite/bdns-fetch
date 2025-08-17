# Makefile for BDNS API project

.PHONY: help install test-integration lint format clean dev-install

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

dev-install: ## Install dependencies including dev dependencies
	poetry install --with dev

test-integration: ## Run integration tests against real BDNS API
	poetry run pytest tests/integration/ -v -s -m integration

test-working: ## Run only the working integration tests (19 tests)
	@echo "🚀 Running BDNS API Integration Tests"
	@echo "======================================"
	@echo ""
	@echo "📋 Running Core Tests (17 tests)..."
	@poetry run pytest tests/integration/test_simple_commands_integration.py \
	                  tests/integration/test_organos_integration.py \
	                  tests/integration/test_enum_commands_integration.py \
	                  tests/integration/test_actividades_integration.py \
	                  tests/integration/test_organos_variants_integration.py \
	                  -v --tb=no -q
	@echo ""
	@echo "📋 Running Additional Working Tests (2 tests)..."
	@poetry run pytest tests/integration/test_document_commands_integration.py -k "convocatorias and not documentos and not pdf" -v --tb=no -q
	@poetry run pytest tests/integration/test_planes_estrategicos_integration.py -k "vigencia" -v --tb=no -q
	@echo ""
	@echo "✅ All working integration tests completed!"
	@echo "📊 Total: 19 working tests for BDNS API commands"

lint: ## Run linting
	poetry run ruff check .

format: ## Format code
	poetry run ruff format .

clean: ## Clean up cache and temporary files
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/
