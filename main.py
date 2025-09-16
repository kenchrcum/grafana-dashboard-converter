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
GRAFANA_CONVERTED_ANNOTATION_ENV = "GRAFANA_CONVERTED_ANNOTATION"
GRAFANA_CONVERSION_MODE_ENV = "GRAFANA_CONVERSION_MODE"
DEFAULT_NAMESPACE = "default"
DEFAULT_CONVERTED_ANNOTATION = "grafana-dashboard-converter/converted-at"
DEFAULT_CONVERSION_MODE = "full"  # Options: "full" or "reference"

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

def get_converted_annotation():
    """Get the converted annotation key from environment variable."""
    annotation = os.getenv(GRAFANA_CONVERTED_ANNOTATION_ENV, DEFAULT_CONVERTED_ANNOTATION)
    logger.info(f"Using converted annotation: {annotation}")
    return annotation

def get_conversion_mode():
    """Get the conversion mode from environment variable."""
    mode = os.getenv(GRAFANA_CONVERSION_MODE_ENV, DEFAULT_CONVERSION_MODE).lower()
    if mode not in ["full", "reference"]:
        logger.warning(f"Invalid conversion mode '{mode}', using default 'full'")
        mode = "full"
    logger.info(f"Using conversion mode: {mode}")
    return mode

def check_existing_grafana_dashboard(name, namespace, clientset, conversion_mode="full"):
    """Check if GrafanaDashboard already exists and determine if it should be updated.
    Returns: (should_skip, mode_changed, existing_dashboard)
    - should_skip: True if dashboard exists and should not be processed
    - mode_changed: True if existing dashboard has different conversion mode
    - existing_dashboard: The existing dashboard object if it exists, None otherwise
    """
    try:
        custom_api = client.CustomObjectsApi(clientset)
        annotation_key = get_converted_annotation()

        # Try to get the existing GrafanaDashboard
        grafana_dashboard = custom_api.get_namespaced_custom_object(
            group="grafana.integreatly.org",
            version="v1beta1",
            namespace=namespace,
            plural="grafanadashboards",
            name=name
        )

        # Check the current conversion mode of the existing dashboard
        labels = grafana_dashboard.get('metadata', {}).get('labels', {})
        existing_mode = labels.get('grafana-dashboard-conversion-mode', 'full')  # Default to 'full' for backward compatibility

        # If the conversion mode has changed, we need to recreate
        if existing_mode != conversion_mode:
            logger.info(f"GrafanaDashboard {namespace}/{name} exists with mode '{existing_mode}' but desired mode is '{conversion_mode}', will recreate")
            return False, True, grafana_dashboard

        # For reference mode, we always want to update to ensure ConfigMap changes are reflected
        if conversion_mode == "reference":
            logger.info(f"GrafanaDashboard {namespace}/{name} exists, will update (reference mode)")
            return False, False, grafana_dashboard

        # For full mode, check the annotation to avoid re-processing
        annotations = grafana_dashboard.get('metadata', {}).get('annotations', {})
        if annotation_key in annotations:
            logger.info(f"GrafanaDashboard {namespace}/{name} already converted (annotation: {annotation_key}), skipping")
            return True, False, grafana_dashboard

        logger.info(f"GrafanaDashboard {namespace}/{name} exists but missing annotation, will update")
        return False, False, grafana_dashboard

    except ApiException as e:
        if e.status == 404:
            # GrafanaDashboard doesn't exist
            logger.info(f"GrafanaDashboard {namespace}/{name} does not exist, will create")
            return False, False, None
        else:
            logger.error(f"Error checking GrafanaDashboard {namespace}/{name}: {e}")
            return False, False, None

def create_grafana_dashboard_crd(configmap, clientset):
    """Create GrafanaDashboard CRDs from ConfigMap. Handles multiple dashboards per ConfigMap."""

    # Find all dashboard JSON files in the ConfigMap data
    dashboard_files = []
    for key, value in configmap.data.items():
        if key == "dashboard.json" or key.endswith(".json"):
            dashboard_files.append((key, value))

    if not dashboard_files:
        logger.warning(f"No dashboard JSON found in ConfigMap {configmap.metadata.name}")
        return

    logger.info(f"Found {len(dashboard_files)} dashboard(s) in ConfigMap {configmap.metadata.name}")

    # Process each dashboard file
    for dashboard_key, dashboard_json in dashboard_files:
        try:
            # Parse the dashboard JSON to extract title
            dashboard_data = json.loads(dashboard_json)
            title = dashboard_data.get("dashboard", {}).get("title", f"{configmap.metadata.name}-{dashboard_key}")

            # Get conversion mode
            conversion_mode = get_conversion_mode()

            # Create unique GrafanaDashboard name based on ConfigMap name and key
            base_name = configmap.metadata.name.lower().replace("_", "-")
            if len(dashboard_files) == 1:
                # If only one dashboard, use the original naming scheme
                grafana_dashboard_name = base_name
            else:
                # If multiple dashboards, include the key in the name
                key_part = dashboard_key.replace(".json", "").replace("_", "-").lower()
                grafana_dashboard_name = f"{base_name}-{key_part}"

            # Check if dashboard already exists and has been converted
            should_skip, mode_changed, existing_dashboard = check_existing_grafana_dashboard(
                grafana_dashboard_name, configmap.metadata.namespace, clientset, conversion_mode
            )

            if should_skip:
                continue  # Skip this dashboard

            # If the conversion mode has changed, delete the existing dashboard first
            if mode_changed and existing_dashboard:
                try:
                    custom_api = client.CustomObjectsApi(clientset)
                    custom_api.delete_namespaced_custom_object(
                        group="grafana.integreatly.org",
                        version="v1beta1",
                        namespace=configmap.metadata.namespace,
                        plural="grafanadashboards",
                        name=grafana_dashboard_name
                    )
                    logger.info(f"Deleted existing GrafanaDashboard {grafana_dashboard_name} due to mode change from '{existing_dashboard.get('metadata', {}).get('labels', {}).get('grafana-dashboard-conversion-mode', 'full')}' to '{conversion_mode}'")
                except ApiException as delete_e:
                    logger.error(f"Failed to delete existing GrafanaDashboard {grafana_dashboard_name}: {delete_e}")
                    continue  # Skip if we can't delete the existing one

            # Get current timestamp for annotation
            import datetime
            converted_at = datetime.datetime.utcnow().isoformat() + "Z"

            # Build the GrafanaDashboard spec based on conversion mode
            grafana_dashboard = {
                "apiVersion": "grafana.integreatly.org/v1beta1",
                "kind": "GrafanaDashboard",
                "metadata": {
                    "name": grafana_dashboard_name,
                    "namespace": configmap.metadata.namespace,
                    "labels": {
                        "app.kubernetes.io/managed-by": "grafana-dashboard-converter",
                        "grafana-dashboard": "converted",
                        "grafana-dashboard-conversion-mode": conversion_mode,
                        "grafana-dashboard-source-configmap": configmap.metadata.name,
                        "grafana-dashboard-source-key": dashboard_key
                    },
                    "annotations": {
                        get_converted_annotation(): converted_at
                    }
                },
                "spec": {
                    "instanceSelector": get_instance_selector()
                }
            }

            if conversion_mode == "full":
                # Full conversion: embed the JSON content
                grafana_dashboard["spec"]["json"] = dashboard_json
                logger.info(f"Creating GrafanaDashboard with embedded JSON content for {dashboard_key}")
            elif conversion_mode == "reference":
                # Reference mode: use ConfigMap reference
                grafana_dashboard["spec"]["configMapRef"] = {
                    "name": configmap.metadata.name,
                    "key": dashboard_key
                }
                # Add resync period for automatic updates
                grafana_dashboard["spec"]["resyncPeriod"] = "10m"
                logger.info(f"Creating GrafanaDashboard with ConfigMap reference for {dashboard_key}")

            # Set folder if specified in labels
            if configmap.metadata.labels and "grafana_folder" in configmap.metadata.labels:
                grafana_dashboard["spec"]["folder"] = configmap.metadata.labels["grafana_folder"]

            # Set allowCrossNamespaceImport for reference mode
            if conversion_mode == "reference" and configmap.metadata.namespace != "default":
                grafana_dashboard["spec"]["allowCrossNamespaceImport"] = True

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
                logger.info(f"Created GrafanaDashboard: {grafana_dashboard_name} with title: '{title}' from {dashboard_key} (mode: {conversion_mode})")
            except ApiException as e:
                if e.status == 409:
                    # Object already exists, try to update it (should only happen in reference mode)
                    try:
                        custom_api.patch_namespaced_custom_object(
                            group="grafana.integreatly.org",
                            version="v1beta1",
                            namespace=configmap.metadata.namespace,
                            plural="grafanadashboards",
                            name=grafana_dashboard_name,
                            body=grafana_dashboard
                        )
                        logger.info(f"Updated GrafanaDashboard: {grafana_dashboard_name} with title: '{title}' from {dashboard_key} (mode: {conversion_mode})")
                    except ApiException as patch_e:
                        logger.error(f"Failed to update GrafanaDashboard {grafana_dashboard_name}: {patch_e}")
                else:
                    logger.error(f"Failed to create GrafanaDashboard {grafana_dashboard_name}: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse dashboard JSON from ConfigMap {configmap.metadata.name}, key {dashboard_key}: {e}")
        except Exception as e:
            logger.error(f"Error processing dashboard from ConfigMap {configmap.metadata.name}, key {dashboard_key}: {e}")

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
