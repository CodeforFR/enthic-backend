.PHONY: clean requirements create_environment

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME := enthic-backend
PYTHON_INTERPRETER := python3
PYTHON_VERSION := 3.8.12
ENV_NAME := $(PROJECT_NAME)-$(PYTHON_VERSION)

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python Dependencies
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements/dev.txt
	pre-commit install

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

create_environment:
	pyenv install -s $(PYTHON_VERSION)
	pyenv virtualenv $(PYTHON_VERSION) $(ENV_NAME)
	pyenv local $(ENV_NAME)
	echo $(ENV_NAME) > .python-version
