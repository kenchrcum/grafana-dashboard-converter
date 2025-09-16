# Grafana Dashboard Converter

A Helm chart for deploying the Grafana Dashboard Converter application that automatically converts legacy ConfigMap-based Grafana dashboards to GrafanaDashboard CRDs compatible with the grafana-operator.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Grafana Operator installed in the cluster

## Installing the Chart

To install the chart with the release name `grafana-dashboard-converter`:

```bash
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter
```

## Configuration

The following table lists the configurable parameters of the Grafana Dashboard Converter chart and their default values.

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

## Namespace Watching Modes

The converter supports two modes for watching ConfigMaps:

### Single Namespace Mode (Default)
```bash
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter \
  --set watchNamespace=my-namespace
```
This mode watches ConfigMaps only in the specified namespace and uses namespace-scoped RBAC permissions.

### Cluster-wide Mode
```bash
helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter \
  --set watchAllNamespaces=true
```
This mode watches ConfigMaps across all namespaces in the cluster and requires cluster-wide RBAC permissions.

## Usage

1. Install the grafana-operator in your cluster
2. Deploy this chart: `helm install grafana-dashboard-converter ./helm/grafana-dashboard-converter`
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
# Trigger release Di 16. Sep 11:40:15 CEST 2025
