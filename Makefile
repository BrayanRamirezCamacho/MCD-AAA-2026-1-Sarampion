#################################################################################
# GLOBALS
#################################################################################

PROJECT_NAME = MCD-AAA-sarampion
PYTHON_INTERPRETER = python

#################################################################################
# COMMANDS
#################################################################################

.PHONY: help requirements data clean lint test_environment

## Show available commands
help:
	@echo "Available rules:"
	@echo "  make test_environment   - Test Python environment"
	@echo "  make requirements       - Install Python dependencies"
	@echo "  make data               - Build processed datasets"
	@echo "  make clean              - Remove compiled Python files"
	@echo "  make lint               - Run flake8"

## Test python environment is setup correctly
test_environment:
	$(PYTHON_INTERPRETER) test_environment.py

## Install Python Dependencies
requirements: test_environment
	$(PYTHON_INTERPRETER) -m pip install --upgrade pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

## Make Dataset
data: requirements
	$(PYTHON_INTERPRETER) src/data/make_dataset.py data/raw data/processed

## Delete all compiled Python files
clean:
	powershell -Command "Get-ChildItem -Recurse -Include *.pyc,*.pyo | Remove-Item -Force"
	powershell -Command "Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force"

## Lint using flake8
lint:
	flake8 src