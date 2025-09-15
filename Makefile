# Makefile for Input Link

.PHONY: help install install-dev test lint format build clean dist-clean

PYTHON := python
PIP := pip
PLATFORM := $(shell python -c "import platform; print(platform.system().lower())")

help: ## Show this help message
	@echo "Input Link - Network Controller Forwarding System"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install package in development mode
	$(PIP) install -e .

install-dev: ## Install with development dependencies
	$(PIP) install -e ".[dev,test,build]"

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src/input_link --cov-report=html --cov-report=term

lint: ## Run linting
	ruff check src tests
	mypy src

format: ## Format code
	black src tests
	isort src tests

build: ## Build executable files
ifeq ($(PLATFORM),windows)
	scripts\build\build.bat
else
	./scripts/build/build.sh
endif

clean: ## Clean build artifacts
	rm -rf build/work/
	rm -rf build/*.spec
	rm -rf build/icons/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

dist-clean: clean ## Clean distribution files
	rm -rf dist/

run-sender: ## Run sender application
	$(PYTHON) -m input_link.apps.sender

run-receiver: ## Run receiver application
	$(PYTHON) -m input_link.apps.receiver

run-gui: ## Run GUI application
	$(PYTHON) -m input_link.apps.gui_main

# Development shortcuts
dev-install: install-dev ## Alias for install-dev

check: lint test ## Run linting and tests

all: format lint test build ## Format, lint, test, and build

# Platform-specific targets
.PHONY: build-windows build-macos

build-windows: ## Build Windows executables (requires Windows)
ifeq ($(PLATFORM),windows)
	scripts\build\build.bat
else
	@echo "Error: Windows build must be run on Windows platform"
	@exit 1
endif

build-macos: ## Build macOS app bundles (requires macOS)
ifeq ($(PLATFORM),darwin)
	./scripts/build/build.sh
else
	@echo "Error: macOS build must be run on macOS platform"
	@exit 1
endif
