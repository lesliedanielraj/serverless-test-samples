# WebSocket API Load Testing with k6

This directory contains k6 load test scripts for testing WebSocket API throttling and performance.

## Prerequisites

1. Install k6:
   - On macOS: `brew install k6`
   - On Windows: `choco install k6`
   - On Linux: [Follow k6 installation guide](https://k6.io/docs/getting-started/installation/)

## Running the Tests

1. Set your WebSocket API endpoint:
   ```bash
   export WS_URL=wss://xs54mshrbi.execute-api.us-east-1.amazonaws.com/prod
   ```

2. Run the load test:
   ```bash
   k6 run websocket_load_test.js
   ```

## Test Scenarios

The load test includes the following stages:
1. Ramp up to 50 users over 30 seconds
2. Maintain 50 users for 1 minute
3. Ramp up to 100 users over 30 seconds
4. Maintain 100 users for 1 minute
5. Ramp down to 0 users over 30 seconds

## Success Criteria

The test will pass if:
- 95% of WebSocket connections are established in less than 1 second
- More than 100 messages are successfully sent during the test

## Monitoring Results

Watch for:
- Connection success rate
- Message delivery success rate
- Any throttling or connection errors
- Response times and latencies

## Troubleshooting

If you encounter throttling:
1. Check the CloudWatch metrics for the WebSocket API
2. Review the API Gateway throttling limits
3. Adjust the test parameters (number of users, ramp-up time) as needed