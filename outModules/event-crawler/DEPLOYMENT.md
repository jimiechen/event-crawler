# Server Deployment Guide

This guide describes how to deploy the Oasis Simulation Server (Python gRPC) and AI Gateway (Rust) using Docker.

## Prerequisites

-   **Docker Desktop** (Mac/Windows) or **Docker Engine** (Linux)
-   **Docker Compose**

## Quick Start

We have provided a deployment script to automate the process.

1.  Navigate to the project root:
    ```bash
    cd /Users/mac/ok-mcp/event-crawler
    ```

2.  Run the deployment script:
    ```bash
    ./scripts/deploy_services.sh
    ```

This script will:
-   Check for Docker installation.
-   Create a default `.env` file for the Python service if missing.
-   Build the Docker images for both services.
-   Start the services in the background.

## Manual Deployment

If you prefer to run `docker compose` manually:

1.  Navigate to the modules directory:
    ```bash
    cd outModules
    ```

2.  Ensure `.env` exists for the Python service:
    ```bash
    # Check open-citycloud/modules/oasis-simulation-server/.env
    ```

3.  Run Docker Compose:
    ```bash
    docker compose up --build -d
    ```

## Verify Deployment

1.  Check running containers:
    ```bash
    docker ps
    ```
    You should see `outmodules-ai-gateway-1` and `outmodules-oasis-service-1`.

2.  Check logs:
    ```bash
    docker compose logs -f
    ```

3.  Test with Verify Script:
    You can run the verification script locally (outside Docker) if you have Python installed, pointing to localhost:3000.
    ```bash
    cd outModules/open-citycloud/modules/oasis-simulation-server
    # Install dependencies locally if needed: pip install requests protobuf
    python3 verify_gateway.py
    ```

## Local Development Setup (Non-Docker)

We provide a script to setup your local environment automatically (install Python dependencies, generate protos, check Rust).

1.  Run the setup script:
    ```bash
    ./scripts/setup_local_env.sh
    ```
    Follow the on-screen instructions. If Rust is missing, it will tell you how to install it.

2.  **Debugging in VS Code**:
    We have included `.vscode/launch.json` configuration.
    -   Open the project in VS Code.
    -   Go to "Run and Debug".
    -   Select "Python: Oasis Server (gRPC)" to debug the Python service.
    -   Select "Rust: AI Gateway" to debug the Gateway (requires "CodeLLDB" extension).

### Manual Setup Details

If you prefer to run manually:
```bash
cd outModules/open-citycloud/modules/oasis-simulation-server
pip install -r requirements.txt
python3 codegen.py
python3 grpc_server.py
```

### 2. Rust Gateway
You need to install Rust:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

Then run:
```bash
cd outModules/MineplanetGo/mineplanet/AiGateway
cargo run
```
