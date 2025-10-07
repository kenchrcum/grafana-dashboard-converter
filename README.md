# Grafana Dashboard Converter

![Version](https://img.shields.io/badge/version-0.3.6-blue.svg)
[![License](https://img.shields.io/badge/license-Unlicense-lightgrey.svg)](LICENSE)
[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/grafana-dashboard-converter)](https://artifacthub.io/packages/search?repo=grafana-dashboard-converter)

A Kubernetes application that automatically converts legacy ConfigMap-based Grafana dashboards to GrafanaDashboard Custom Resources compatible with the [grafana-operator](https://github.com/grafana-operator/grafana-operator).

## 🎯 Overview

This project addresses the migration from the old sidecar-based Grafana dashboard deployment pattern to the modern grafana-operator approach. The converter watches for ConfigMaps labeled with `grafana_dashboard=1` and automatically creates corresponding `GrafanaDashboard` CRDs.

### Key Features

- 🔄 **Automatic Conversion**: Watches ConfigMaps and creates GrafanaDashboard CRDs
- 🏷️ **Label-based Discovery**: Uses `grafana_dashboard=1` label for ConfigMap identification
- 🎛️ **Dual Conversion Modes**: Full embedding or ConfigMap reference modes
- 📁 **Multi-dashboard Support**: Single or multiple dashboards per ConfigMap
- 🔒 **Security First**: Non-root execution, read-only filesystem, minimal RBAC
- 🚀 **Production Ready**: Health checks, resource limits, comprehensive monitoring
- 📦 **Helm Integration**: Complete Helm chart for easy deployment
- 🌐 **Cross-namespace Support**: Configurable namespace isolation

## 🏗️ Architecture

- **Converter Application**: Python application that watches Kubernetes ConfigMaps
- **Docker Container**: Multi-stage build with security best practices
- **Kubernetes Deployment**: Includes RBAC, health checks, and security best practices
- **Helm Chart**: Complete deployment and configuration management

## 🚀 Quick Start

### Prerequisites

- ✅ Kubernetes cluster (v1.19+)
- ✅ [grafana-operator](https://github.com/grafana-operator/grafana-operator) installed
- ✅ Helm 3.x
- ✅ kubectl configured

### Installation

#### Option 1: Public Helm Repository (Recommended)

```bash
# Add the public Helm repository
helm repo add grafana-dashboard-converter https://kenchrcum.github.io/grafana-dashboard-converter/

# Update your local Helm chart repository cache
helm repo update

# Install the chart
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter

# Verify deployment
kubectl get pods -l app.kubernetes.io/name=grafana-dashboard-converter
```

#### Option 2: Local Helm Chart (Development)

```bash
# Install from local directory
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter

# Or with custom configuration
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter \
  --set watchNamespace=monitoring \
  --set grafana.conversionMode=reference
```

#### Option 3: Custom Docker Image

```bash
# Build your own image
docker build -t your-registry/grafana-dashboard-converter:latest .

# Push to registry
docker push your-registry/grafana-dashboard-converter:latest

# Deploy with custom image
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter \
  --set image.repository=your-registry/grafana-dashboard-converter \
  --set image.tag=latest
```

### Configuration

#### Namespace Watching

The converter can watch specific namespaces or all namespaces:

**Single Namespace (Default):**
```bash
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set watchNamespace=monitoring
```

**All Namespaces (Requires Cluster RBAC):**
```bash
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set watchAllNamespaces=true
```

#### Grafana Instance Selection

Configure which Grafana instances receive the dashboards:

```bash
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set grafana.instanceSelector.matchLabels.app=grafana \
  --set grafana.instanceSelector.matchLabels.environment=production
```

#### Conversion Modes

Choose the right conversion mode for your use case:

**Full Mode (Default)** - Embeds JSON directly in CRD:
```bash
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set grafana.conversionMode=full
```

**Reference Mode** - References ConfigMap for live updates:
```bash
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set grafana.conversionMode=reference \
  --set grafana.dashboard.resyncPeriod=5m
```

### Usage Examples

#### 1. Create Your First Dashboard

```bash
# Apply example ConfigMap
kubectl apply -f examples/sample-dashboard-configmap.yaml

# Check conversion results
kubectl get grafanadashboards
kubectl describe grafanadashboard sample-grafana-dashboard
```

#### 2. Multiple Dashboards per ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: monitoring-dashboards
  labels:
    grafana_dashboard: "1"
    grafana_folder: "Monitoring"
data:
  system-overview.json: |
    { "dashboard": { "title": "System Overview", ... } }
  kubernetes-cluster.json: |
    { "dashboard": { "title": "Kubernetes Cluster", ... } }
```

#### 3. Environment Variables Configuration

```bash
# Set custom conversion mode
export GRAFANA_CONVERSION_MODE=reference
export GRAFANA_DASHBOARD_RESYNC_PERIOD=5m

# Run locally for testing
python main.py
```

#### 4. Monitoring and Troubleshooting

```bash
# Check converter logs
kubectl logs -l app.kubernetes.io/name=grafana-dashboard-converter

# Check health endpoints
kubectl port-forward deployment/grafana-dashboard-converter 8080:8080
curl http://localhost:8080/health
curl http://localhost:8080/ready

# Monitor conversion metrics
kubectl get grafanadashboards --watch
```

## ⚙️ Conversion Modes

The converter supports two modes for creating GrafanaDashboard resources:

### Full Mode (Default)
Creates GrafanaDashboard resources with embedded JSON content:

```yaml
spec:
  json: |
    {
      "dashboard": {
        "title": "My Dashboard",
        ...
      }
    }
```

**Benefits:**
- 🔒 **Self-contained**: Dashboard content embedded in CRD
- 🗑️ **Immutable**: Works even if ConfigMap is deleted
- ⚡ **Optimized**: Annotation-based processing prevention

**Best for:**
- Static dashboards that don't change often
- Environments where ConfigMaps may be cleaned up
- Self-contained resource preferences

### Reference Mode
Creates GrafanaDashboard resources that reference the original ConfigMap:

```yaml
spec:
  configMapRef:
    name: my-legacy-dashboard
    key: dashboard.json
  resyncPeriod: 10m
  allowCrossNamespaceImport: true
```

**Benefits:**
- 🔄 **Live sync**: Dashboard updates when ConfigMap changes
- 💾 **Efficient**: Content stays in ConfigMap, no duplication
- 📡 **Real-time**: Changes propagate automatically

**Best for:**
- Active dashboard development and maintenance
- Environments with frequent dashboard updates
- Storage efficiency requirements

### Configuration

**Set conversion mode via Helm:**
```bash
# Full mode (default)
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set grafana.conversionMode=full

# Reference mode with custom resync
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set grafana.conversionMode=reference \
  --set grafana.dashboard.resyncPeriod=5m
```

**Environment variables:**
```bash
export GRAFANA_CONVERSION_MODE=reference
export GRAFANA_DASHBOARD_RESYNC_PERIOD=5m
```

**Mode switching:** When switching between modes, the converter automatically deletes and recreates GrafanaDashboard resources to prevent conflicts.

## 📋 Dashboard Examples

Create ConfigMaps with your existing Grafana dashboards using the `grafana_dashboard=1` label.

### Single Dashboard ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-legacy-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
    grafana_folder: "Monitoring"
data:
  dashboard.json: |
    {
      "dashboard": {
        "id": null,
        "title": "My Dashboard",
        "tags": ["templated"],
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "Sample Panel",
            "type": "graph",
            "targets": [
              {
                "expr": "up",
                "legendFormat": "{{job}}",
                "refId": "A"
              }
            ]
          }
        ],
        "time": {
          "from": "now-6h",
          "to": "now"
        },
        "refresh": "5s"
      }
    }
```

### Multiple Dashboards ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-dashboards
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
    grafana_folder: "Loki"
data:
  loki-chunks.json: |
    {
      "dashboard": {
        "title": "Loki Chunks",
        "description": "Loki chunk storage metrics"
      }
    }
  loki-logs.json: |
    {
      "dashboard": {
        "title": "Loki Logs",
        "description": "Loki log processing metrics"
      }
    }
  loki-operational.json: |
    {
      "dashboard": {
        "title": "Loki Operational",
        "description": "Loki operational health"
      }
    }
```

**Note:** Multiple dashboards per ConfigMap are converted to separate GrafanaDashboard CRDs named like `loki-dashboards-loki-chunks`.

## 🔍 Verification

After creating ConfigMaps, verify the conversion process:

```bash
# List all converted dashboards
kubectl get grafanadashboards

# Check specific dashboard details
kubectl describe grafanadashboard my-legacy-dashboard

# Check conversion logs
kubectl logs -l app.kubernetes.io/name=grafana-dashboard-converter --tail=50
```

### Expected Results

**Full Mode Dashboard:**
```yaml
apiVersion: grafana.integreatly.org/v1beta1
kind: GrafanaDashboard
metadata:
  name: my-legacy-dashboard
  namespace: monitoring
  labels:
    grafana-dashboard: converted
    grafana-dashboard-conversion-mode: full
    grafana-dashboard-source-configmap: my-legacy-dashboard
spec:
  json: |-
    {
      "dashboard": {
        "title": "My Dashboard",
        ...
      }
    }
  allowCrossNamespaceImport: true
  instanceSelector:
    matchLabels:
      dashboards: grafana
```

**Reference Mode Dashboard:**
```yaml
apiVersion: grafana.integreatly.org/v1beta1
kind: GrafanaDashboard
metadata:
  name: loki-dashboards-loki-chunks
  labels:
    grafana-dashboard-conversion-mode: reference
    grafana-dashboard-source-configmap: loki-dashboards
    grafana-dashboard-source-key: loki-chunks.json
spec:
  configMapRef:
    name: loki-dashboards
    key: loki-chunks.json
  resyncPeriod: "10m"
  allowCrossNamespaceImport: true
  instanceSelector:
    matchLabels:
      dashboards: grafana
```

## 🚨 Troubleshooting

### Common Issues

#### 1. **RBAC Permissions**
```bash
# Check if service account exists and has permissions
kubectl get serviceaccount grafana-dashboard-converter
kubectl auth can-i get configmaps --as=system:serviceaccount:default:grafana-dashboard-converter

# Check cluster role for all-namespace watching
kubectl get clusterrole grafana-dashboard-converter
```

**Solution:** Ensure RBAC is properly configured:
```bash
# For namespace-scoped
kubectl apply -f helm/grafana-dashboard-converter/templates/role.yaml

# For cluster-scoped
kubectl apply -f helm/grafana-dashboard-converter/templates/clusterrole.yaml
```

#### 2. **ConfigMap Not Found**
```bash
# Check ConfigMap exists and has correct label
kubectl get configmap my-dashboard -o yaml

# Verify label is present
kubectl label configmap my-dashboard grafana_dashboard=1
```

#### 3. **GrafanaDashboard Creation Fails**
```bash
# Check grafana-operator is running
kubectl get deployment grafana-operator

# Check CRD exists
kubectl get crd grafanadashboards.grafana.integreatly.org

# Check converter logs for specific errors
kubectl logs -l app.kubernetes.io/name=grafana-dashboard-converter
```

#### 4. **Health Check Failures**
```bash
# Test health endpoints directly
kubectl port-forward deployment/grafana-dashboard-converter 8080:8080
curl http://localhost:8080/health
curl http://localhost:8080/ready

# Check resource limits
kubectl describe pod -l app.kubernetes.io/name=grafana-dashboard-converter
```

#### 5. **Mode Switching Issues**
```bash
# Manual cleanup if needed
kubectl delete grafanadashboard old-dashboard-name
kubectl annotate configmap my-dashboard grafana-dashboard-converter/converted-at-
```

### Debug Commands

```bash
# Comprehensive status check
kubectl get pods,svc,configmap,grafanadashboard -l grafana_dashboard=1

# Check events for failures
kubectl get events --sort-by=.metadata.creationTimestamp

# Validate dashboard JSON
python3 -c "import json; json.load(open('dashboard.json'))"

# Test Kubernetes API access
kubectl auth can-i create grafanadashboards --as=system:serviceaccount:default:grafana-dashboard-converter
```

### Getting Help

1. Check the [grafana-operator documentation](https://github.com/grafana-operator/grafana-operator)
2. Review the [troubleshooting guide](https://github.com/grafana-operator/grafana-operator/blob/master/docs/troubleshooting.md)
3. Open an issue with:
   - Converter version (`kubectl exec deployment/grafana-dashboard-converter -- python main.py --version`)
   - Kubernetes version (`kubectl version`)
   - grafana-operator version
   - Relevant logs from converter and operator

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
| `image.tag` | Docker image tag | `0.3.6` |
| `image.pullPolicy` | Image pull policy | `Always` |
| `replicaCount` | Number of replicas | `1` |
| `watchNamespace` | Namespace to watch for ConfigMaps (defaults to release namespace) | `""` |
| `watchAllNamespaces` | Watch ConfigMaps across all namespaces | `false` |
| `grafana.instanceSelector.matchLabels` | Labels used to match Grafana instances for dashboard deployment | `{"dashboards": "grafana"}` |
| `grafana.convertedAnnotation` | Annotation key to mark converted dashboards (prevents re-processing) | `grafana-dashboard-converter/converted-at` |
| `grafana.conversionMode` | Conversion mode: "full" (embed JSON) or "reference" (use ConfigMap reference) | `full` |
| `grafana.dashboard.allowCrossNamespaceImport` | Allow cross-namespace import for dashboards | `true` |
| `grafana.dashboard.resyncPeriod` | Resync period for dashboards | `10m` |
| `resources.limits.cpu` | CPU limit | `100m` |
| `resources.limits.memory` | Memory limit | `128Mi` |
| `resources.requests.cpu` | CPU request | `50m` |
| `resources.requests.memory` | Memory request | `64Mi` |
| `rbac.create` | Create RBAC resources | `true` |
| `rbac.clusterRole.create` | Create cluster role for cluster-wide RBAC | `true` |
| `serviceAccount.create` | Create service account | `true` |
| `serviceAccount.name` | Service account name | `""` |
| `serviceAccount.annotations` | Service account annotations | `{}` |
| `healthCheck.enabled` | Enable health checks | `true` |
| `healthCheck.port` | Health check port | `8080` |
| `healthCheck.livenessProbe.initialDelaySeconds` | Initial delay for liveness probe | `30` |
| `healthCheck.livenessProbe.periodSeconds` | Period for liveness probe | `30` |
| `healthCheck.livenessProbe.timeoutSeconds` | Timeout for liveness probe | `5` |
| `healthCheck.livenessProbe.failureThreshold` | Failure threshold for liveness probe | `3` |
| `healthCheck.readinessProbe.initialDelaySeconds` | Initial delay for readiness probe | `5` |
| `healthCheck.readinessProbe.periodSeconds` | Period for readiness probe | `10` |
| `healthCheck.readinessProbe.timeoutSeconds` | Timeout for readiness probe | `5` |
| `healthCheck.readinessProbe.failureThreshold` | Failure threshold for readiness probe | `3` |
| `podSecurityContext.fsGroup` | Pod security context fsGroup | `10001` |
| `securityContext.allowPrivilegeEscalation` | Allow privilege escalation | `false` |
| `securityContext.readOnlyRootFilesystem` | Read-only root filesystem | `true` |
| `securityContext.runAsNonRoot` | Run as non-root user | `true` |
| `securityContext.runAsUser` | Run as user ID | `10001` |
| `securityContext.capabilities.drop` | Dropped capabilities | `["ALL"]` |
| `nodeSelector` | Node labels for pod assignment | `{}` |
| `tolerations` | Tolerations for pod assignment | `[]` |
| `affinity` | Affinity rules for pod assignment | `{}` |
| `podLabels` | Additional labels for pods | `{}` |
| `podAnnotations` | Additional annotations for pods | `{}` |

### Environment Variables

- `NAMESPACE`: Namespace to watch for ConfigMaps (defaults to pod's namespace)
- `WATCH_ALL_NAMESPACES`: Enable watching across all namespaces (default: false)
- `GRAFANA_INSTANCE_SELECTOR`: JSON string defining labels to match Grafana instances (default: `{"matchLabels":{"dashboards":"grafana"}}`)
- `GRAFANA_CONVERTED_ANNOTATION`: Annotation key to mark converted dashboards (default: `grafana-dashboard-converter/converted-at`)
- `GRAFANA_CONVERSION_MODE`: Conversion mode ("full" or "reference") (default: "full")
- `GRAFANA_DASHBOARD_ALLOW_CROSS_NAMESPACE`: Allow cross-namespace import for dashboards (default: "true")
- `GRAFANA_DASHBOARD_RESYNC_PERIOD`: Resync period for dashboards (default: "10m")

## 🛠️ Development

### Prerequisites

- Python 3.8+
- Docker (for containerized development)
- Kubernetes cluster with kubectl configured
- Helm 3.x

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/kenchrcum/grafana-dashboard-converter.git
cd grafana-dashboard-converter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest  # If tests exist

# Run locally with your kubeconfig
python main.py

# Or run with custom configuration
NAMESPACE=monitoring GRAFANA_CONVERSION_MODE=reference python main.py
```

### Development with Docker

```bash
# Build development image
docker build -t grafana-dashboard-converter:dev .

# Run with volume mount for live reload
docker run -it --rm \
  -v $(pwd):/app \
  -e KUBECONFIG=/app/kubeconfig \
  grafana-dashboard-converter:dev
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=main --cov-report=html

# Test specific functionality
pytest tests/test_conversion.py -v
```

### Code Quality

```bash
# Install development tools
pip install black flake8 mypy

# Format code
black main.py

# Lint code
flake8 main.py

# Type checking
mypy main.py
```

## 📚 API Reference

### Health Check Endpoints

The application exposes health check endpoints for Kubernetes probes:

#### `GET /health`
Returns the overall health status of the application.

**Response:**
```json
{
  "status": "OK"
}
```

**Status Codes:**
- `200`: Healthy
- `503`: Unhealthy

#### `GET /ready`
Returns the readiness status of the application.

**Response:**
```json
{
  "status": "Ready"
}
```

**Status Codes:**
- `200`: Ready to accept traffic
- `503`: Not ready

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NAMESPACE` | Kubernetes namespace to watch | Release namespace | No |
| `WATCH_ALL_NAMESPACES` | Watch all namespaces | `false` | No |
| `GRAFANA_INSTANCE_SELECTOR` | JSON selector for Grafana instances | `{"matchLabels":{"dashboards":"grafana"}}` | No |
| `GRAFANA_CONVERTED_ANNOTATION` | Annotation key for processed dashboards | `grafana-dashboard-converter/converted-at` | No |
| `GRAFANA_CONVERSION_MODE` | Conversion mode (`full` or `reference`) | `full` | No |
| `GRAFANA_DASHBOARD_ALLOW_CROSS_NAMESPACE` | Allow cross-namespace imports | `true` | No |
| `GRAFANA_DASHBOARD_RESYNC_PERIOD` | Resync period for reference mode | `10m` | No |

### Labels and Annotations

#### ConfigMap Labels
- `grafana_dashboard: "1"` - Marks ConfigMap for conversion
- `grafana_folder: "FolderName"` - Sets dashboard folder in Grafana

#### GrafanaDashboard Labels
- `grafana-dashboard: converted` - Indicates successful conversion
- `grafana-dashboard-conversion-mode: full|reference` - Conversion mode used
- `grafana-dashboard-source-configmap: name` - Source ConfigMap name
- `grafana-dashboard-source-key: key` - Source ConfigMap key

#### Annotations
- `grafana-dashboard-converter/converted-at` - ISO timestamp of conversion

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
# Add the public Helm repository
helm repo add grafana-dashboard-converter https://kenchrcum.github.io/grafana-dashboard-converter/

# Update your local Helm chart repository cache
helm repo update

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
