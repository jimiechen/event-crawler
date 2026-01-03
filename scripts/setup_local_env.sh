#!/bin/bash

# Setup Local Development Environment
# This script helps install dependencies for running services locally (without Docker).

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
MODULES_DIR="$PROJECT_ROOT/outModules"

echo -e "${GREEN}=== Setting up Local Environment ===${NC}"

# 1. Python Setup
echo -e "\n${YELLOW}[1/3] Checking Python Environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed.${NC}"
    exit 1
fi

PYTHON_SERVICE_DIR="$MODULES_DIR/open-citycloud/modules/oasis-simulation-server"
if [ -d "$PYTHON_SERVICE_DIR" ]; then
    echo "Installing Python dependencies..."
    # Check if pip3 is available
    PIP_CMD="pip3"
    if ! command -v pip3 &> /dev/null; then
        PIP_CMD="pip"
    fi
    
    $PIP_CMD install -r "$PYTHON_SERVICE_DIR/requirements.txt"
    
    echo "Generating Python Protobuf files..."
    cd "$PYTHON_SERVICE_DIR"
    python3 codegen.py
    cd "$PROJECT_ROOT"
else
    echo -e "${RED}Error: Python service directory not found at $PYTHON_SERVICE_DIR${NC}"
    exit 1
fi

# 2. Rust Setup
echo -e "\n${YELLOW}[2/3] Checking Rust Environment...${NC}"
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}Error: Rust/Cargo is not installed.${NC}"
    echo -e "${YELLOW}Please install Rust using the following command:${NC}"
    echo -e "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo -e "Then run: source \"\$HOME/.cargo/env\""
    echo -e "After installing, re-run this script."
    # We cannot proceed with Rust build if cargo is missing
    exit 1
else
    echo "Rust is installed: $(cargo --version)"
fi

# 3. Rust Build
echo -e "\n${YELLOW}[3/3] Building Rust Gateway...${NC}"
RUST_GATEWAY_DIR="$MODULES_DIR/MineplanetGo/mineplanet/AiGateway"
if [ -d "$RUST_GATEWAY_DIR" ]; then
    cd "$RUST_GATEWAY_DIR"
    # Ensure build.rs has correct relative path for local dev (which is ../../../protocols)
    # The Dockerfile modified it, but local checkout should be clean or we should ensure it's correct.
    # The original code had "../../../protocols" which is correct for local layout:
    # outModules/MineplanetGo/mineplanet/AiGateway/build.rs
    # outModules/protocols
    # Depth: AiGateway(1) -> mineplanet(2) -> MineplanetGo(3) -> outModules(4).
    # Wait, let's count:
    # build.rs is in AiGateway.
    # ../ -> mineplanet
    # ../../ -> MineplanetGo
    # ../../../ -> outModules
    # ../../../protocols -> outModules/protocols.
    # So the path is correct.
    
    echo "Building Rust project..."
    cargo build
    cd "$PROJECT_ROOT"
else
    echo -e "${RED}Error: Rust Gateway directory not found at $RUST_GATEWAY_DIR${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo "You can now run services locally."
echo "Python Service: cd outModules/open-citycloud/modules/oasis-simulation-server && python3 grpc_server.py"
echo "Rust Gateway:   cd outModules/MineplanetGo/mineplanet/AiGateway && cargo run"
