#!/bin/bash
# Docker-based installation testing
# Provides completely isolated environment for each test run

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "UFPS Docker Test Environment"
echo "======================================"
echo ""

# Build test container
echo -e "${YELLOW}Building test container...${NC}"
docker build -f Dockerfile.test -t ufps-test .

# Run tests in container
echo -e "${YELLOW}Running tests in isolated environment...${NC}"
docker run --rm -it ufps-test

# Optional: Test on different Python versions
if [ "$1" = "--all-versions" ]; then
    for version in 3.8 3.9 3.10 3.11; do
        echo ""
        echo -e "${YELLOW}Testing with Python $version...${NC}"
        
        # Create temporary Dockerfile
        sed "s/FROM python:3.9-slim/FROM python:$version-slim/" Dockerfile.test > Dockerfile.test.$version
        
        # Build and run
        docker build -f Dockerfile.test.$version -t ufps-test:py$version .
        docker run --rm ufps-test:py$version
        
        # Cleanup
        rm Dockerfile.test.$version
    done
fi

echo ""
echo -e "${GREEN}Docker testing complete!${NC}"