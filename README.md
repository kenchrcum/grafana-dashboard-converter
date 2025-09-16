# Grafana Dashboard Converter

A Kubernetes application that automatically converts legacy ConfigMap-based Grafana dashboards to GrafanaDashboard Custom Resources compatible with the [grafana-operator](https://github.com/grafana-operator/grafana-operator).

## Overview

This project addresses the migration from the old sidecar-based Grafana dashboard deployment pattern to the modern grafana-operator approach. The converter watches for ConfigMaps labeled with `grafana_dashboard=1` and automatically creates corresponding `GrafanaDashboard` CRDs.

## Architecture

- **Converter Application**: Python application that watches Kubernetes ConfigMaps
- **Docker Container**: Python-based container with dependencies
- **Kubernetes Deployment**: Includes RBAC, health checks, and security best practices
- **Helm Chart**: Easy deployment and configuration management

## Quick Start

### Prerequisites

- Kubernetes cluster with grafana-operator installed
- Helm 3.x
- Docker (for building the image)
- Python 3.8+ (for local development)

### 1. Build and Push the Docker Image

```bash
# Build the image for Docker Hub
docker build -t kenchrcum/grafana-dashboard-converter:latest .

# Push to Docker Hub
docker push kenchrcum/grafana-dashboard-converter:latest
```

### 2. Deploy with Helm

```bash
# Install the chart
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter

# Or install from a registry (after publishing)
helm repo add my-repo https://my-helm-repo.com
helm install grafana-dashboard-converter my-repo/grafana-dashboard-converter
```

### 3. Configure Namespace Watching

You can configure the converter to watch either a specific namespace or all namespaces:

**Watch specific namespace (default):**
```bash
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter \
  --set watchNamespace=my-namespace
```

**Watch all namespaces:**
```bash
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter \
  --set watchAllNamespaces=true
```

### 4. Create Legacy ConfigMaps

Create ConfigMaps with your existing Grafana dashboards:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-legacy-dashboard
  labels:
    grafana_dashboard: "1"
    grafana_folder: "Monitoring"
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "My Dashboard",
        "panels": [...]
      }
    }
```

### 5. Verify Conversion

The converter will automatically create a corresponding GrafanaDashboard CRD:

```bash
kubectl get grafanadashboards
```

## Project Structure

```
.
├── main.py                             # Main converter application
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Python container build
├── .dockerignore                       # Docker build exclusions
├── .gitignore                          # Git ignore patterns
├── k8s/                                # Raw Kubernetes manifests
│   ├── rbac.yaml                       # Cluster-wide RBAC configuration
│   ├── rbac-namespace.yaml             # Namespace-scoped RBAC configuration
│   └── deployment.yaml                 # Deployment manifest
├── helm/                               # Helm chart
│   └── grafana-dashboard-converter/
│       ├── Chart.yaml                  # Helm chart metadata
│       ├── values.yaml                 # Default configuration values
│       ├── charts/                     # Chart dependencies (empty)
│       ├── templates/                  # Kubernetes resource templates
│       │   ├── _helpers.tpl            # Helm template helpers
│       │   ├── serviceaccount.yaml     # Service account template
│       │   ├── clusterrole.yaml        # Cluster role template
│       │   ├── clusterrolebinding.yaml # Cluster role binding template
│       │   ├── role.yaml               # Namespaced role template
│       │   ├── rolebinding.yaml        # Namespaced role binding template
│       │   └── deployment.yaml         # Deployment template
│       └── README.md                   # Helm chart documentation
├── examples/                           # Sample ConfigMaps
│   ├── sample-dashboard-configmap.yaml
│   └── cluster-wide-dashboard-configmap.yaml
├── build.sh                           # Build script for Docker images
└── deploy.sh                         # Deployment script
```

## Configuration

### Helm Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Docker image repository | `kenchrcum/grafana-dashboard-converter` |
| `image.tag` | Docker image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `Always` |
| `replicaCount` | Number of replicas | `1` |
| `watchNamespace` | Namespace to watch for ConfigMaps (defaults to release namespace) | `""` |
| `watchAllNamespaces` | Watch ConfigMaps across all namespaces | `false` |
| `resources.limits.cpu` | CPU limit | `100m` |
| `resources.limits.memory` | Memory limit | `128Mi` |
| `resources.requests.cpu` | CPU request | `50m` |
| `resources.requests.memory` | Memory request | `64Mi` |
| `rbac.create` | Create RBAC resources | `true` |
| `serviceAccount.create` | Create service account | `true` |
| `serviceAccount.name` | Service account name | `""` |
| `healthCheck.enabled` | Enable health checks | `true` |
| `healthCheck.port` | Health check port | `8080` |
| `podSecurityContext.fsGroup` | Pod security context fsGroup | `10001` |
| `securityContext.allowPrivilegeEscalation` | Allow privilege escalation | `false` |
| `securityContext.readOnlyRootFilesystem` | Read-only root filesystem | `true` |
| `securityContext.runAsNonRoot` | Run as non-root user | `true` |
| `securityContext.runAsUser` | Run as user ID | `10001` |

### Environment Variables

- `NAMESPACE`: Namespace to watch for ConfigMaps (defaults to pod's namespace)
- `WATCH_ALL_NAMESPACES`: Enable watching across all namespaces (default: false)

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires kubeconfig)
python main.py

# Or run with custom kubeconfig
KUBECONFIG=~/.kube/config python main.py

# Run with environment variables
NAMESPACE=my-namespace python main.py
```

### Building for Production

```bash
# Build Docker image for Docker Hub
docker build -t kenchrcum/grafana-dashboard-converter:v1.0.0 .

# Or build with specific Python version
docker build --build-arg PYTHON_VERSION=3.11 -t kenchrcum/grafana-dashboard-converter:v1.0.0 .

# Push to Docker Hub
docker push kenchrcum/grafana-dashboard-converter:v1.0.0
```

## CI/CD

This project includes GitHub Actions workflows for automated testing and deployment. Docker images are built locally and pushed to Docker Hub.

### Workflows

#### Helm Chart Release (`helm.yml`)
Manages Helm chart releases and GitHub Pages hosting:

- **Triggers**: Changes to `helm/` directory on `main`/`master`
- **Features**:
  - Chart linting and validation
  - Automatic chart packaging and release creation
  - GitHub Pages deployment for Helm repository hosting

#### Helm Testing (`helm-test.yml`)
Validates Helm charts on every change:

- **Triggers**: Changes to `helm/` directory
- **Tests**: YAML validation, Helm linting, template rendering

#### GitHub Pages Setup (`setup-pages.yml`)
One-time setup for Helm repository hosting:

- **Trigger**: Manual workflow dispatch
- **Creates**: `gh-pages` branch with initial repository structure

### Docker Image Management

Docker images are built locally and pushed to Docker Hub (`kenchrcum/grafana-dashboard-converter`).

#### Building and Pushing Images

```bash
# Build locally
docker build -t kenchrcum/grafana-dashboard-converter:latest .

# Push to Docker Hub
docker push kenchrcum/grafana-dashboard-converter:latest

# Or use the provided build script (recommended)
./build.sh                                    # Build only
TAG=v1.0.0 ./build.sh                         # Build with specific tag
PUSH=true ./build.sh                          # Build and push
TAG=v1.0.0 PUSH=true ./build.sh               # Build specific version and push

# Alternative: Use deploy script
./deploy.sh                                    # Builds locally
PUSH_TO_DOCKER_HUB=true ./deploy.sh           # Builds and pushes to Docker Hub
```

### Setup Instructions

1. **Setup GitHub Pages for Helm Repository**:
   ```bash
   # Go to repository Settings > Pages
   # Set source to "GitHub Actions"
   # Then run the setup-pages workflow manually
   ```

2. **Repository Settings**:
   - Go to **Settings > Actions > General**
   - Set **Workflow permissions** to "Read and write permissions"
   - Enable **Allow GitHub Actions to create and approve pull requests** (optional)

### Using the Published Assets

#### Docker Images
```bash
# Pull from Docker Hub
docker pull kenchrcum/grafana-dashboard-converter:latest

# Or use in Kubernetes
image: kenchrcum/grafana-dashboard-converter:latest
```

#### Helm Charts
```bash
# Add the GitHub Pages repository
helm repo add grafana-dashboard-converter https://kenneth.github.io/grafana-dashboard-converter/

# Install the chart
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter
```

## Security

The application follows Kubernetes security best practices:

- Non-root user execution
- Read-only root filesystem
- Minimal RBAC permissions
- Resource limits and requests
- Health checks for liveness and readiness

## Troubleshooting

### Check Logs

```bash
# Get deployment logs
kubectl logs -l app.kubernetes.io/name=grafana-dashboard-converter

# Check pod status
kubectl get pods -l app.kubernetes.io/name=grafana-dashboard-converter
```

### Common Issues

1. **RBAC Permissions**: Ensure the service account has permissions to read ConfigMaps and create GrafanaDashboard CRDs
2. **Image Pull**: Verify the Docker image is accessible from your cluster
3. **Namespace Configuration**: Check that `watchNamespace` or `watchAllNamespaces` is configured correctly
4. **Cluster-wide Mode**: If using `watchAllNamespaces=true`, ensure cluster-admin permissions are available

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under The Unlicense - see the LICENSE file for details.
