#!/usr/bin/env node
import serverInstance from './server';
import nativeMessagingHostInstance from './native-messaging-host';
import { NATIVE_SERVER_PORT } from './constant';

async function startServer() {
  try {
    console.log('Starting MCP HTTP Server...');
    
    // Set up the relationship between server and native host
    serverInstance.setNativeHost(nativeMessagingHostInstance);
    nativeMessagingHostInstance.setServer(serverInstance);
    
    // Start the HTTP server directly
    await serverInstance.start(NATIVE_SERVER_PORT, nativeMessagingHostInstance);
    
    console.log(`MCP HTTP Server started successfully on port ${NATIVE_SERVER_PORT}`);
    console.log(`Server is accessible at: http://127.0.0.1:${NATIVE_SERVER_PORT}`);
    
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Handle process signals
process.on('SIGINT', async () => {
  console.log('\nShutting down server...');
  try {
    await serverInstance.stop();
    console.log('Server stopped successfully');
    process.exit(0);
  } catch (error) {
    console.error('Error stopping server:', error);
    process.exit(1);
  }
});

process.on('SIGTERM', async () => {
  console.log('\nShutting down server...');
  try {
    await serverInstance.stop();
    console.log('Server stopped successfully');
    process.exit(0);
  } catch (error) {
    console.error('Error stopping server:', error);
    process.exit(1);
  }
});

startServer();