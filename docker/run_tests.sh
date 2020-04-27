#!/usr/bin/env bash

set -e

pytest tests --cov-report html

echo "Running MyPy"
# mypy composte tests

echo "Starting Black..."
black --quiet composte tests

echo "Starting flake8..."
# flake8 composte tests

echo "Starting bandit..."
# bandit -r composte

echo "Starting import sorting..."
isort --recursive --apply composte tests

echo "Starting pydocstyle..."
pydocstyle composte tests
