#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Grafana Dashboard Converter Deployment Script${NC}"
echo "================================================="

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl is not installed. Please install kubectl first.${NC}"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo -e "${RED}Helm is not installed. Please install Helm first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
DOCKER_REPO="kenchrcum/grafana-dashboard-converter"
DOCKER_TAG="${DOCKER_TAG:-latest}"
docker build -t ${DOCKER_REPO}:${DOCKER_TAG} .
echo -e "${GREEN}✓ Docker image built as ${DOCKER_REPO}:${DOCKER_TAG}${NC}"

# Optional: Push to Docker Hub
if [ "${PUSH_TO_DOCKER_HUB}" = "true" ]; then
    echo -e "${YELLOW}Pushing to Docker Hub...${NC}"
    docker push ${DOCKER_REPO}:${DOCKER_TAG}
    echo -e "${GREEN}✓ Image pushed to Docker Hub${NC}"
fi

# Check Kubernetes connection
echo -e "${YELLOW}Checking Kubernetes connection...${NC}"
kubectl cluster-info
echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"

# Deploy with Helm
echo -e "${YELLOW}Deploying with Helm...${NC}"
helm upgrade --install grafana-dashboard-converter ./helm/grafana-dashboard-converter

# Wait for deployment
echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/grafana-dashboard-converter

echo -e "${GREEN}✓ Deployment successful!${NC}"

# Show status
echo -e "${YELLOW}Deployment status:${NC}"
kubectl get pods -l app.kubernetes.io/name=grafana-dashboard-converter
kubectl get svc -l app.kubernetes.io/name=grafana-dashboard-converter

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Create ConfigMaps with grafana_dashboard=1 label"
echo "2. Check logs: kubectl logs -l app.kubernetes.io/name=grafana-dashboard-converter"
echo "3. Verify GrafanaDashboard CRDs are created"
echo ""
echo -e "${GREEN}Example ConfigMap creation:${NC}"
echo "kubectl apply -f examples/sample-dashboard-configmap.yaml"
echo ""
echo -e "${YELLOW}Alternative deployment modes:${NC}"
echo ""
echo -e "${YELLOW}For single namespace watching:${NC}"
echo "helm upgrade --install grafana-dashboard-converter ./helm/grafana-dashboard-converter \\"
echo "  --set watchNamespace=my-namespace"
echo ""
echo -e "${YELLOW}For cluster-wide watching:${NC}"
echo "helm upgrade --install grafana-dashboard-converter ./helm/grafana-dashboard-converter \\"
echo "  --set watchAllNamespaces=true"
echo ""
echo -e "${YELLOW}Usage examples:${NC}"
echo ""
echo -e "${YELLOW}Build with custom tag:${NC}"
echo "DOCKER_TAG=v1.0.0 ./deploy.sh"
echo ""
echo -e "${YELLOW}Build and push to Docker Hub:${NC}"
echo "PUSH_TO_DOCKER_HUB=true ./deploy.sh"
echo ""
echo -e "${YELLOW}Build and push specific version:${NC}"
echo "DOCKER_TAG=v1.0.0 PUSH_TO_DOCKER_HUB=true ./deploy.sh"
