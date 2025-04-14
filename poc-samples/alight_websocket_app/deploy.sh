cdk destroy AlightApiStack

cdk deploy AlightBedrockAgentStack
cdk deploy AlightApiStack

# Make the sync script executable
chmod +x ./sync_kb.sh

# Run the knowledge base sync after deployment
echo "Starting knowledge base sync..."
./sync_kb.sh
