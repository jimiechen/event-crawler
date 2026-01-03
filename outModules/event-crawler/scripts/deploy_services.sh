#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Deployment for Mineplanet Services...${NC}"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker Desktop for Mac: https://docs.docker.com/desktop/install/mac-install/"
    exit 1
fi

# Check for Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not available.${NC}"
    exit 1
fi

# Navigate to project root (assuming script is run from project root or scripts folder)
# We need to be in outModules where docker-compose.yml is
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DEPLOY_ROOT="$SCRIPT_DIR/../../outModules"

if [ ! -f "$DEPLOY_ROOT/docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found in $DEPLOY_ROOT${NC}"
    exit 1
fi

cd "$DEPLOY_ROOT"

# Check .env for Python service
OASIS_ENV="open-citycloud/modules/oasis-simulation-server/.env"
if [ ! -f "$OASIS_ENV" ]; then
    echo -e "${RED}Warning: $OASIS_ENV not found.${NC}"
    echo "Creating from example..."
    # Ensure directory exists
    mkdir -p $(dirname "$OASIS_ENV")
    # Write default env
    echo "DEEPSEEK_API_KEY=sk-561f49b3c780407d84f8228c0db971be" > "$OASIS_ENV"
    echo "DEEPSEEK_API_BASE=https://api.deepseek.com/v1" >> "$OASIS_ENV"
    echo "DEEPSEEK_MODEL=deepseek-chat" >> "$OASIS_ENV"
fi

# Export env vars for docker-compose to pick up (if using variable substitution)
set -a
source "$OASIS_ENV"
set +a

echo -e "${GREEN}Building and Starting Services...${NC}"
docker compose up --build -d

echo -e "${GREEN}Services Deployed!${NC}"
echo "Rust Gateway: http://localhost:3000"
echo "Python gRPC:  localhost:50051"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop:"
echo "  docker compose down"
