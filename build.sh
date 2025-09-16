#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

REPO="kenchrcum/grafana-dashboard-converter"
TAG="${TAG:-latest}"

echo -e "${BLUE}Grafana Dashboard Converter - Build Script${NC}"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

echo -e "${YELLOW}Building Docker image...${NC}"
echo -e "${BLUE}Repository:${NC} $REPO"
echo -e "${BLUE}Tag:${NC} $TAG"
echo ""

# Build the image
docker build -t ${REPO}:${TAG} .

# Build additional tags if specified
if [ -n "$ADDITIONAL_TAGS" ]; then
    echo -e "${YELLOW}Building additional tags...${NC}"
    for additional_tag in $ADDITIONAL_TAGS; do
        docker tag ${REPO}:${TAG} ${REPO}:${additional_tag}
        echo -e "${GREEN}✓ Tagged ${REPO}:${additional_tag}${NC}"
    done
fi

echo -e "${GREEN}✓ Docker image built successfully: ${REPO}:${TAG}${NC}"

# Push to Docker Hub if requested
if [ "$PUSH" = "true" ] || [ "$PUSH_TO_DOCKER_HUB" = "true" ]; then
    echo ""
    echo -e "${YELLOW}Pushing to Docker Hub...${NC}"

    # Check if user is logged in to Docker Hub
    if ! docker info | grep -q "Username"; then
        echo -e "${RED}Error: Not logged in to Docker Hub. Please run 'docker login' first.${NC}"
        echo -e "${YELLOW}Usage: docker login -u kenchrcum${NC}"
        exit 1
    fi

    docker push ${REPO}:${TAG}
    echo -e "${GREEN}✓ Pushed ${REPO}:${TAG} to Docker Hub${NC}"

    # Push additional tags if they exist
    if [ -n "$ADDITIONAL_TAGS" ]; then
        for additional_tag in $ADDITIONAL_TAGS; do
            docker push ${REPO}:${additional_tag}
            echo -e "${GREEN}✓ Pushed ${REPO}:${additional_tag} to Docker Hub${NC}"
        done
    fi
fi

echo ""
echo -e "${GREEN}Build completed successfully!${NC}"
echo ""
echo -e "${BLUE}Usage examples:${NC}"
echo "  ./build.sh                                    # Build only"
echo "  TAG=v1.0.0 ./build.sh                         # Build with specific tag"
echo "  PUSH=true ./build.sh                          # Build and push"
echo "  TAG=v1.0.0 PUSH=true ./build.sh               # Build specific version and push"
echo "  ADDITIONAL_TAGS=\"latest dev\" TAG=v1.0.0 PUSH=true ./build.sh  # Multiple tags"
