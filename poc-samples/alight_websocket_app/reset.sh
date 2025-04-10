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

# Optional: Clear Poetry environment
echo "Clearing Poetry environment..."
rm -rf .venv/

# Optional: Recreate Poetry environment
echo "Recreating Poetry environment..."
poetry env use python3.12
poetry install

# Install handlers dependencies
echo "Installing handlers dependencies..."
cd handlers
poetry build
cd ..

echo "Redeploying all stacks with CDK..."
cdk synth
cdk deploy --all --require-approval never

echo "Reset complete!"
