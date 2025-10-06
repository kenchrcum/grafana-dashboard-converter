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

For detailed configuration options, please refer to the chart's [values.yaml](https://github.com/kenchrcum/grafana-dashboard-converter/blob/main/helm/grafana-dashboard-converter/values.yaml) file in the main repository.

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