#!/bin/bash

# Destroy all stacks
echo "Destroying all stacks..."
cdk destroy --all --force

# Clear CDK cache
echo "Clearing CDK cache..."
rm -rf cdk.out/
rm -rf .cdk.staging/

# Clear Python cache
echo "Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -r {} +
rm -rf .pytest_cache/

# Clear CDK context
echo "Clearing CDK context..."
rm -f cdk.context.json

# Clear asset files
echo "Clearing asset files..."
rm -rf asset.*

# Optional: Clear virtual environment
echo "Clearing virtual environment..."
rm -rf .venv/

# Optional: Recreate virtual environment
echo "Recreating virtual environment..."
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo "Reset complete!"
