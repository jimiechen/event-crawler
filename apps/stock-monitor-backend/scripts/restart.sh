#!/bin/bash

# Ensure we are in the project root directory
# Assuming the script is run from the project root or resides there
cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to kill process on port
kill_port() {
    PORT=$1
    echo "Checking port $PORT..."
    # Find PIDs using lsof
    PIDS=$(lsof -t -i:$PORT)
    if [ ! -z "$PIDS" ]; then
        echo "Found process(es) on port $PORT: $PIDS. Killing..."
        # Kill the processes
        kill -9 $PIDS
        
        # Wait for processes to exit
        echo "Waiting for processes to exit..."
        for i in {1..10}; do
            if [ -z "$(lsof -t -i:$PORT)" ]; then
                echo "Port $PORT is now free."
                return 0
            fi
            sleep 1
        done
        
        # Final check
        if [ ! -z "$(lsof -t -i:$PORT)" ]; then
             echo "WARNING: Failed to kill processes on port $PORT. Manual intervention required."
             exit 1
        fi
    else
        echo "No process found on port $PORT."
    fi
}

# Kill existing processes on 8000 and 8002
kill_port 8000
#kill_port 8002

# Wait a moment to ensure ports are freed
sleep 10

# Start services
echo "Starting service on port 8000..."
nohup ./venv/bin/python -u run_new.py --env development --host 0.0.0.0 --port 8000 --reload --simple-reload --log-level info > logs/server_8000.log 2>&1 &
PID_8000=$!

# Wait to verify startup
echo "Waiting for service to start (PID: $PID_8000)..."
sleep 5
if ps -p $PID_8000 > /dev/null; then
   echo "Service on port 8000 started with PID $PID_8000. Logs: logs/server_8000.log"
else
   echo "ERROR: Service failed to start. Check logs/server_8000.log for details."
   cat logs/server_8000.log
   exit 1
fi

#echo "Starting service on port 8002..."
#nohup python3 run.py --port 8002 > logs/server_8002.log 2>&1 &
#PID_8002=$!
#echo "Service on port 8002 started with PID $PID_8002. Logs: logs/server_8002.log"

echo "All services restarted successfully."
