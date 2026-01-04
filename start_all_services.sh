#!/bin/bash

# start_all_services.sh
# 启动所有相关服务：Native Server (3000), Backend (8000)

echo "Starting Stock Monitor Backend (Port 8000)..."
cd apps/stock-monitor-backend || exit
nohup python3 run.py --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID. Logs: apps/stock-monitor-backend/backend.log"

cd ../.. || exit

echo "Starting n8n-demo (Port 5173)..."
cd n8n-demo || exit
nohup node server.js > n8n_demo.log 2>&1 &
N8N_PID=$!
echo "n8n-demo started with PID $N8N_PID. Logs: n8n-demo/n8n_demo.log"

cd .. || exit

echo "All services started!"
echo "Backend PID: $BACKEND_PID"
echo "n8n-demo PID: $N8N_PID"
echo "Check logs for details."
