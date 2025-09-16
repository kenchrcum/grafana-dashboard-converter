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
# Build the image
docker build -t grafana-dashboard-converter:latest .

# Push to your registry
docker tag grafana-dashboard-converter:latest your-registry/grafana-dashboard-converter:latest
docker push your-registry/grafana-dashboard-converter:latest
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
└── deploy.sh                         # Deployment script
```

## Configuration

### Helm Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Docker image repository | `grafana-dashboard-converter` |
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
# Build Docker image
docker build -t grafana-dashboard-converter:v1.0.0 .

# Or build with specific Python version
docker build --build-arg PYTHON_VERSION=3.11 -t grafana-dashboard-converter:v1.0.0 .
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
