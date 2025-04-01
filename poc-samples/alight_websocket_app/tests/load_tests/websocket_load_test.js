import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Stay at 50 users for 1 minute
    { duration: '30s', target: 100 }, // Ramp up to 100 users over 30 seconds
    { duration: '30s', target: 100 },  // Stay at 100 users for 30 seconds
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    'ws_connecting': ['p(95)<1000'], // 95% of connection times should be below 1s
    'ws_msgs_sent': ['count>100'],   // Should send more than 100 messages
  },
};

// Get WebSocket URL from environment variable or use default
const WS_URL = __ENV.WS_URL || 'wss://your-api-id.execute-api.region.amazonaws.com/prod';

export default function() {
  // WebSocket connection test
  const response = ws.connect(WS_URL, {}, function(socket) {
    // Connection successful
    socket.on('open', () => {
      console.log('Connected to WebSocket');
      
      // Create a promise to wait for the response
      const responsePromise = new Promise((resolve) => {
        socket.on('message', (data) => {
          console.log('Received message:', data);
          check(data, {
            'message received': (d) => d !== ''
          });
          resolve();
        });
      });
      
      // Send a test message
      socket.send(JSON.stringify({
          'action': 'sendmessage',  // This needs to match the route key in API Gateway
          'data': {
              'message': 'How many days in a year?',
              'type': 'chat'
          }
      }));
      
      // Wait for the response with a timeout
      Promise.race([
        responsePromise,
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout waiting for response')), 5000))
      ]).catch(error => {
        console.error('Error:', error.toString());
      });
    });

    // Note: Message handling is now done in the promise above

    // Handle any errors
    socket.on('error', (e) => {
      console.log('Error:', e.toString());
    });

    // Keep connection alive for a few seconds then close
    sleep(5);
    socket.close();
  });

  // Verify the connection was successful
  check(response, { 'status is 101': (r) => r && r.status === 101 });
}