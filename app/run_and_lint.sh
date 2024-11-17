#!/bin/bash

# Run Ruff linter
echo "Running Ruff check..."
ruff check . --output-format=github

echo "Done."

# Run the Python application
echo "Running application.py..."
python application.py


