# Grafana Dashboard Converter

A Helm chart for deploying the Grafana Dashboard Converter application that automatically converts legacy ConfigMap-based Grafana dashboards to GrafanaDashboard CRDs compatible with the grafana-operator.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Grafana Operator installed in the cluster

## Installing the Chart

### Option 1: Install from GitHub Pages (Recommended)

Add the Helm repository and install the chart:

```bash
# Add the repository
helm repo add grafana-dashboard-converter https://kenneth.github.io/grafana-dashboard-converter/

# Update your local Helm chart repository cache
helm repo update

# Install the chart
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter
```

### Option 2: Install from Local Directory

To install the chart from the local directory with the release name `grafana-dashboard-converter`:

```bash
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter
```

## Configuration

The following table lists the configurable parameters of the Grafana Dashboard Converter chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Docker image repository | `kenchrcum/grafana-dashboard-converter` |
| `image.tag` | Docker image tag | `0.3.2` |
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
| `serviceAccount.create` | Create service account | `true` |
| `serviceAccount.name` | Service account name | `""` |
| `healthCheck.enabled` | Enable health checks | `true` |
| `healthCheck.port` | Health check port | `8080` |
| `podSecurityContext.fsGroup` | Pod security context fsGroup | `10001` |
| `securityContext.allowPrivilegeEscalation` | Allow privilege escalation | `false` |
| `securityContext.readOnlyRootFilesystem` | Read-only root filesystem | `true` |
| `securityContext.runAsNonRoot` | Run as non-root user | `true` |
| `securityContext.runAsUser` | Run as user ID | `10001` |

## Namespace Watching Modes

The converter supports two modes for watching ConfigMaps:

### Single Namespace Mode (Default)
```bash
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set watchNamespace=my-namespace
```
This mode watches ConfigMaps only in the specified namespace and uses namespace-scoped RBAC permissions.

### Cluster-wide Mode
```bash
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter \
  --set watchAllNamespaces=true
```
This mode watches ConfigMaps across all namespaces in the cluster and requires cluster-wide RBAC permissions.

## Usage

1. Install the grafana-operator in your cluster
2. Deploy this chart: `helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter`
3. Create ConfigMaps with your legacy Grafana dashboards, labeled with `grafana_dashboard=1`
4. The converter will automatically create corresponding GrafanaDashboard CRDs

### Example ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-dashboard
  labels:
    grafana_dashboard: "1"
    grafana_folder: "General"
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "My Dashboard",
        ...
      }
    }
```

## Building and Pushing the Image

```bash
# Build the Docker image
docker build -t kenchrcum/grafana-dashboard-converter:latest .

# Push to Docker Hub
docker push kenchrcum/grafana-dashboard-converter:latest
```

The image is automatically configured in the `values.yaml` file to use the Docker Hub repository.
