#!/bin/bash

# start_all_services.sh
# 启动所有相关服务：Native Server (3000), Backend (8000)

echo "Starting Stock Monitor Backend (Port 8000)..."
cd apps/stock-monitor-backend || exit
nohup python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID. Logs: apps/stock-monitor-backend/backend.log"

cd ../.. || exit

echo "Starting Native Server (Port 3000)..."
cd apps/native-server || exit
nohup npm start > native_server.log 2>&1 &
NATIVE_PID=$!
echo "Native Server started with PID $NATIVE_PID. Logs: apps/native-server/native_server.log"

cd ../.. || exit

echo "All services started!"
echo "Backend PID: $BACKEND_PID"
echo "Native Server PID: $NATIVE_PID"
echo "Check logs for details."
