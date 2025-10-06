# Grafana Dashboard Converter Helm Repository

[![Helm](https://img.shields.io/badge/Helm-3.0+-blue.svg)](https://helm.sh/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Welcome to the official Helm repository for the Grafana Dashboard Converter! This repository hosts Helm charts that make it easy to deploy the Grafana Dashboard Converter operator on Kubernetes clusters.

## 🚀 Quick Start

### Add the Repository

```bash
helm repo add grafana-dashboard-converter https://kenchrcum.github.io/grafana-dashboard-converter/
helm repo update
```

### Install the Chart

Install the latest version of the Grafana Dashboard Converter:

```bash
helm install grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter
```

### Upgrade

To upgrade to the latest version:

```bash
helm repo update
helm upgrade grafana-dashboard-converter grafana-dashboard-converter/grafana-dashboard-converter
```

## 📦 Available Charts

| Chart | Description | Latest Version |
|-------|-------------|----------------|
| `grafana-dashboard-converter` | Deploys the Grafana Dashboard Converter operator to convert and manage Grafana dashboards in Kubernetes | `0.3.5` |

## 🔧 Configuration

The following table lists all configurable parameters of the `grafana-dashboard-converter` chart and their default values. For more details, refer to the chart's [values.yaml](https://github.com/kenchrcum/grafana-dashboard-converter/blob/main/helm/grafana-dashboard-converter/values.yaml) file.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Docker image repository for the Grafana Dashboard Converter | `kenchrcum/grafana-dashboard-converter` |
| `image.tag` | Docker image tag | `"0.3.5"` |
| `image.pullPolicy` | Image pull policy | `Always` |
| `replicaCount` | Number of replicas for the deployment | `1` |
| `watchNamespace` | Namespace to watch for ConfigMaps (leave empty for all namespaces if `watchAllNamespaces` is true) | `""` |
| `watchAllNamespaces` | Whether to watch all namespaces | `false` |
| `resources.limits.cpu` | CPU resource limit | `100m` |
| `resources.limits.memory` | Memory resource limit | `128Mi` |
| `resources.requests.cpu` | CPU resource request | `50m` |
| `resources.requests.memory` | Memory resource request | `64Mi` |
| `podSecurityContext.fsGroup` | File system group for the pod | `10001` |
| `securityContext.allowPrivilegeEscalation` | Allow privilege escalation | `false` |
| `securityContext.readOnlyRootFilesystem` | Read-only root filesystem | `true` |
| `securityContext.runAsNonRoot` | Run as non-root user | `true` |
| `securityContext.runAsUser` | User ID to run as | `10001` |
| `securityContext.capabilities.drop` | List of capabilities to drop | `["ALL"]` |
| `serviceAccount.create` | Create a service account | `true` |
| `serviceAccount.annotations` | Annotations for the service account | `{}` |
| `serviceAccount.name` | Name of the service account (auto-generated if empty) | `""` |
| `rbac.create` | Create RBAC resources | `true` |
| `rbac.clusterRole.create` | Create cluster role | `true` |
| `healthCheck.enabled` | Enable health check probes | `true` |
| `healthCheck.port` | Port for health checks | `8080` |
| `healthCheck.livenessProbe.initialDelaySeconds` | Initial delay for liveness probe | `30` |
| `healthCheck.livenessProbe.periodSeconds` | Period for liveness probe | `30` |
| `healthCheck.livenessProbe.timeoutSeconds` | Timeout for liveness probe | `5` |
| `healthCheck.livenessProbe.failureThreshold` | Failure threshold for liveness probe | `3` |
| `healthCheck.readinessProbe.initialDelaySeconds` | Initial delay for readiness probe | `5` |
| `healthCheck.readinessProbe.periodSeconds` | Period for readiness probe | `10` |
| `healthCheck.readinessProbe.timeoutSeconds` | Timeout for readiness probe | `5` |
| `healthCheck.readinessProbe.failureThreshold` | Failure threshold for readiness probe | `3` |
| `nodeSelector` | Node selector for pod scheduling | `{}` |
| `tolerations` | Tolerations for pod scheduling | `[]` |
| `affinity` | Affinity rules for pod scheduling | `{}` |
| `podLabels` | Additional labels for pods | `{}` |
| `podAnnotations` | Additional annotations for pods | `{}` |
| `grafana.instanceSelector.matchLabels` | Labels to match Grafana instances | `{"dashboards": "grafana"}` |
| `grafana.convertedAnnotation` | Annotation to mark converted dashboards | `"grafana-dashboard-converter/converted-at"` |
| `grafana.conversionMode` | Conversion mode: "full" (embed JSON) or "reference" (use ConfigMap reference) | `"full"` |
| `grafana.dashboard.allowCrossNamespaceImport` | Allow cross-namespace import for dashboards | `true` |
| `grafana.dashboard.resyncPeriod` | Resync period for dashboards in reference mode | `"10m"` |

## 📖 What is Grafana Dashboard Converter?

The Grafana Dashboard Converter is a Kubernetes operator that helps convert and manage Grafana dashboards within your cluster. It provides an automated way to handle dashboard conversions, making it easier to maintain and deploy Grafana configurations across environments.

## 🤝 Contributing

We welcome contributions! Please see the [main repository](https://github.com/kenchrcum/grafana-dashboard-converter) for contribution guidelines.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/kenchrcum/grafana-dashboard-converter/blob/main/LICENSE) file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/kenchrcum/grafana-dashboard-converter)
- [Issues](https://github.com/kenchrcum/grafana-dashboard-converter/issues)
- [Releases](https://github.com/kenchrcum/grafana-dashboard-converter/releases)

---

*Maintained by [kenchrcum](https://github.com/kenchrcum)*