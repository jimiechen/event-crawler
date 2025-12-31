const serverModule = require('./dist/server');
const { NATIVE_SERVER_PORT } = require('./dist/constant');

const serverInstance = serverModule.default;

async function main() {
  try {
    await serverInstance.start(NATIVE_SERVER_PORT);
    console.log(`HTTP server started on port ${NATIVE_SERVER_PORT}`);
  } catch (error) {
    console.error('Failed to start HTTP server:', error);
    process.exit(1);
  }
}

main();
