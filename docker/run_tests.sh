#!/usr/bin/env bash

set -e

pytest tests --cov-report html

echo "Running MyPy"
mypy .

echo "Starting Black..."
black --quiet composte tests

echo "Starting flake8..."
flake8 .

echo "Starting bandit..."
bandit -r .

echo "Starting import sorting..."
isort --recursive --apply .

echo "Starting pydocstyle..."
pydocstyle composte tests
