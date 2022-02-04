.PHONY: clean requirements create_environment

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME := enthic-backend
ENV_NAME := $(PROJECT_NAME)-$(PYTHON_VERSION)

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python Dependencies
dev_requirements:
	. venv/bin/activate
	pip3 install -U pip setuptools wheel
	pip3 install -r requirements/dev.txt
	pre-commit install

prod_requirements:
	. venv/bin/activate
	pip3 install -U pip setuptools wheel
	pip3 install -r requirements/prod.txt

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

create_environment:
	pip3 install virtualenv
	virtualenv venv -p python3

activate:
	. venv/bin/activate
