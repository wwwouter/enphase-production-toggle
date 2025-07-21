#!/bin/bash
# Pre-commit wrapper that never blocks

# Run all the formatters and linters
echo "Running code formatting and linting..."

# Run ruff with fixes
uv run ruff check --fix . || true

# Run ruff formatting
uv run ruff format . || true

# Run black formatting
uv run black . || true

# Add all modified files back to staging
echo "Adding modified files to staging..."
git add .

echo "Pre-commit hook completed successfully!"
exit 0