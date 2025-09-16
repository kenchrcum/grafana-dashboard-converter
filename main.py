#!/usr/bin/env python3

import os
import json
import logging
import signal
import sys
from typing import Optional
import threading
import time

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from flask import Flask, jsonify
import requests

# Constants
GRAFANA_DASHBOARD_LABEL = "grafana_dashboard=1"
NAMESPACE_ENV = "NAMESPACE"
WATCH_ALL_NAMESPACES_ENV = "WATCH_ALL_NAMESPACES"
GRAFANA_INSTANCE_SELECTOR_ENV = "GRAFANA_INSTANCE_SELECTOR"
DEFAULT_NAMESPACE = "default"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default instance selector if not configured
DEFAULT_INSTANCE_SELECTOR = {
    "matchLabels": {
        "dashboards": "grafana"
    }
}

# Global variables for health checks
healthy = True
ready = False

# Flask app for health checks
app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    if healthy:
        return jsonify({"status": "OK"}), 200
    else:
        return jsonify({"status": "Unhealthy"}), 503

@app.route('/ready')
def readiness_check():
    """Readiness check endpoint."""
    if ready:
        return jsonify({"status": "Ready"}), 200
    else:
        return jsonify({"status": "Not Ready"}), 503

def load_kubernetes_config():
    """Load Kubernetes configuration."""
    try:
        # Try to load in-cluster config first
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration")
    except config.ConfigException:
        # Fall back to kubeconfig
        config.load_kube_config()
        logger.info("Loaded kubeconfig from file")

def get_instance_selector():
    """Get the instance selector configuration from environment variable."""
    selector_json = os.getenv(GRAFANA_INSTANCE_SELECTOR_ENV)
    if selector_json:
        try:
            selector = json.loads(selector_json)
            logger.info(f"Using configured instance selector: {selector}")
            return selector
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse GRAFANA_INSTANCE_SELECTOR: {e}, using default")
    else:
        logger.info("GRAFANA_INSTANCE_SELECTOR not set, using default")

    return DEFAULT_INSTANCE_SELECTOR

def create_grafana_dashboard_crd(configmap, clientset):
    """Create GrafanaDashboard CRD from ConfigMap."""

    # Find the dashboard JSON in the ConfigMap data
    dashboard_json = None
    for key, value in configmap.data.items():
        if key == "dashboard.json" or key.endswith(".json"):
            dashboard_json = value
            break

    if not dashboard_json:
        logger.warning(f"No dashboard JSON found in ConfigMap {configmap.metadata.name}")
        return

    try:
        # Parse the dashboard JSON to extract title
        dashboard_data = json.loads(dashboard_json)
        title = dashboard_data.get("dashboard", {}).get("title", configmap.metadata.name)

        # Create GrafanaDashboard CRD
        grafana_dashboard_name = configmap.metadata.name.lower().replace("_", "-")

        grafana_dashboard = {
            "apiVersion": "grafana.integreatly.org/v1beta1",
            "kind": "GrafanaDashboard",
            "metadata": {
                "name": grafana_dashboard_name,
                "namespace": configmap.metadata.namespace,
                "labels": {
                    "app.kubernetes.io/managed-by": "grafana-dashboard-converter",
                    "grafana-dashboard": "converted"
                }
            },
            "spec": {
                "json": dashboard_json,
                "instanceSelector": get_instance_selector()
            }
        }

        # Set folder if specified in labels
        if configmap.metadata.labels and "grafana_folder" in configmap.metadata.labels:
            grafana_dashboard["spec"]["folder"] = configmap.metadata.labels["grafana_folder"]

        # Try to create the GrafanaDashboard CRD
        try:
            custom_api = client.CustomObjectsApi(clientset)
            custom_api.create_namespaced_custom_object(
                group="grafana.integreatly.org",
                version="v1beta1",
                namespace=configmap.metadata.namespace,
                plural="grafanadashboards",
                body=grafana_dashboard
            )
            logger.info(f"Created GrafanaDashboard: {grafana_dashboard_name} with title: {title}")
        except ApiException as e:
            if e.status == 409:
                # Object already exists, try to update it
                try:
                    custom_api.patch_namespaced_custom_object(
                        group="grafana.integreatly.org",
                        version="v1beta1",
                        namespace=configmap.metadata.namespace,
                        plural="grafanadashboards",
                        name=grafana_dashboard_name,
                        body=grafana_dashboard
                    )
                    logger.info(f"Updated GrafanaDashboard: {grafana_dashboard_name} with title: {title}")
                except ApiException as patch_e:
                    logger.error(f"Failed to update GrafanaDashboard {grafana_dashboard_name}: {patch_e}")
            else:
                logger.error(f"Failed to create GrafanaDashboard {grafana_dashboard_name}: {e}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse dashboard JSON from ConfigMap {configmap.metadata.name}: {e}")
    except Exception as e:
        logger.error(f"Error processing ConfigMap {configmap.metadata.name}: {e}")

def watch_configmaps():
    """Watch ConfigMaps for changes."""
    global ready

    try:
        load_kubernetes_config()
        clientset = client.CoreV1Api()

        watch_all_namespaces = os.getenv(WATCH_ALL_NAMESPACES_ENV, "false").lower() == "true"
        namespace = os.getenv(NAMESPACE_ENV, DEFAULT_NAMESPACE)

        if watch_all_namespaces:
            logger.info("Starting Grafana Dashboard Converter watching ALL namespaces")
            namespace = ""  # Empty string means all namespaces
        else:
            logger.info(f"Starting Grafana Dashboard Converter in namespace: {namespace}")

        logger.info(f"Watching for ConfigMaps with label: {GRAFANA_DASHBOARD_LABEL}")

        # Create watch object
        w = watch.Watch()
        resource_version = None

        # Mark as ready once we start watching
        ready = True
        logger.info("Grafana Dashboard Converter is ready")

        while True:
            try:
                # Watch ConfigMaps
                if watch_all_namespaces:
                    stream = w.stream(
                        clientset.list_config_map_for_all_namespaces,
                        label_selector=GRAFANA_DASHBOARD_LABEL,
                        resource_version=resource_version
                    )
                else:
                    stream = w.stream(
                        clientset.list_namespaced_config_map,
                        namespace=namespace,
                        label_selector=GRAFANA_DASHBOARD_LABEL,
                        resource_version=resource_version
                    )

                for event in stream:
                    event_type = event['type']
                    configmap = event['object']

                    if event_type in ['ADDED', 'MODIFIED']:
                        logger.info(f"Processing ConfigMap: {configmap.metadata.namespace}/{configmap.metadata.name}")
                        create_grafana_dashboard_crd(configmap, client.ApiClient())
                    elif event_type == 'DELETED':
                        logger.info(f"ConfigMap deleted: {configmap.metadata.namespace}/{configmap.metadata.name}")

                    # Update resource version for efficient watching
                    if configmap.metadata.resource_version:
                        resource_version = configmap.metadata.resource_version

            except ApiException as e:
                if e.status == 410:  # Gone - resource version is too old
                    logger.warning("Resource version is too old, restarting watch")
                    resource_version = None
                else:
                    logger.error(f"API exception: {e}")
                    time.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(5)  # Wait before retrying

    except Exception as e:
        logger.error(f"Failed to start ConfigMap watcher: {e}")
        sys.exit(1)

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global healthy, ready
    logger.info("Received shutdown signal, stopping gracefully...")
    healthy = False
    ready = False
    sys.exit(0)

def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start ConfigMap watcher in a separate thread
    watcher_thread = threading.Thread(target=watch_configmaps, daemon=True)
    watcher_thread.start()

    # Start Flask app for health checks
    logger.info("Starting health server on :8080")
    app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == "__main__":
    main()
