#!/usr/bin/env python3
"""
Input validation and sanitization module for Grafana Dashboard Converter.

This module provides comprehensive validation and sanitization for:
- JSON schema validation for dashboard structure
- Input sanitization for all user-provided data
- ConfigMap data validation before processing
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
import html

logger = logging.getLogger(__name__)

# Basic Grafana Dashboard JSON Schema
# This is a simplified schema that covers the essential structure
DASHBOARD_SCHEMA = {
    "type": "object",
    "required": ["dashboard"],
    "properties": {
        "dashboard": {
            "type": "object",
            "required": ["title"],
            "properties": {
                "id": {"oneOf": [{"type": "null"}, {"type": "number"}]},
                "title": {"type": "string", "minLength": 1, "maxLength": 200},
                "tags": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": 50},
                    "maxItems": 50
                },
                "timezone": {"type": "string", "maxLength": 100},
                "panels": {
                    "type": "array",
                    "items": {"type": "object"},
                    "maxItems": 1000
                },
                "time": {"type": "object"},
                "timepicker": {"type": "object"},
                "templating": {"type": "object"},
                "annotations": {"type": "object"},
                "refresh": {"type": "string", "maxLength": 50},
                "schemaVersion": {"type": "number"},
                "version": {"type": "number"},
                "links": {"type": "array"},
                "folder": {"type": "string", "maxLength": 200},
                "uid": {"type": "string", "maxLength": 100},
                "description": {"type": "string", "maxLength": 5000}
            },
            "additionalProperties": True  # Allow additional Grafana-specific properties
        }
    },
    "additionalProperties": False
}

# Kubernetes resource name validation pattern
# RFC 1123 subdomain: lowercase alphanumeric characters, '-' or '.', must start and end with alphanumeric
K8S_NAME_PATTERN = re.compile(r'^[a-z0-9]([a-z0-9\-.]*[a-z0-9])?$')

# Kubernetes label key pattern: DNS subdomain prefix (optional) / name
# Format: [prefix/]name where prefix is DNS subdomain and name can have underscores
# Examples: app.kubernetes.io/managed-by, app.kubernetes.io/name, my-label, grafana_dashboard
# Note: Kubernetes allows underscores in label names but not in DNS subdomains
K8S_LABEL_KEY_PATTERN = re.compile(r'^([a-z0-9]([-a-z0-9.]*[a-z0-9])?/)?[a-z0-9]([-a-z0-9_]*[a-z0-9])?$')

# Kubernetes label value pattern: alphanumeric with dashes, underscores, dots
# Can contain uppercase and lowercase letters, starts and ends with alphanumeric
K8S_LABEL_VALUE_PATTERN = re.compile(r'^[a-zA-Z0-9]([-a-zA-Z0-9._]*[a-zA-Z0-9])?$')

# Annotation key pattern: DNS subdomain prefix (optional) / name
# Same format as label keys but can be longer (up to 253 chars for the key)
K8S_ANNOTATION_KEY_PATTERN = re.compile(r'^([a-z0-9]([-a-z0-9.]*[a-z0-9])?/)?[a-z0-9]([-a-z0-9]*[a-z0-9])?$')

# Folder name pattern (allow spaces and special characters for Grafana folders)
FOLDER_NAME_PATTERN = re.compile(r'^[\w\s\-_.()]{1,100}$')


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class SanitizationError(Exception):
    """Custom exception for sanitization errors."""
    pass


def validate_dashboard_json(dashboard_json: str) -> Tuple[bool, Optional[str]]:
    """
    Validate dashboard JSON structure.
    
    Supports two formats:
    1. Wrapped format: {"dashboard": {"title": "...", "panels": [...]}}
    2. Direct format: {"title": "...", "panels": [...]}
    
    Args:
        dashboard_json: JSON string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Parse JSON
        dashboard_data = json.loads(dashboard_json)
        
        # Basic structure validation
        if not isinstance(dashboard_data, dict):
            return False, "Dashboard JSON must be an object"
        
        # Handle both wrapped and direct formats
        if "dashboard" in dashboard_data:
            # Wrapped format: {"dashboard": {...}}
            dashboard_obj = dashboard_data["dashboard"]
            if not isinstance(dashboard_obj, dict):
                return False, "Dashboard 'dashboard' key must be an object"
        else:
            # Direct format: dashboard is the root object
            dashboard_obj = dashboard_data
        
        # Validate required fields
        if "title" not in dashboard_obj:
            return False, "Dashboard must have a 'title' field"
        
        title = dashboard_obj["title"]
        if not isinstance(title, str) or len(title) == 0:
            return False, "Dashboard title must be a non-empty string"
        
        if len(title) > 200:
            return False, "Dashboard title must be 200 characters or less"
        
        # Validate schema version if present
        if "schemaVersion" in dashboard_obj:
            schema_version = dashboard_obj["schemaVersion"]
            if not isinstance(schema_version, (int, float)):
                return False, "Dashboard schemaVersion must be a number"
        
        # Validate panels if present
        if "panels" in dashboard_obj:
            panels = dashboard_obj["panels"]
            if not isinstance(panels, list):
                return False, "Dashboard panels must be an array"
            if len(panels) > 1000:
                return False, "Dashboard cannot have more than 1000 panels"
        
        # Validate refresh time if present
        if "refresh" in dashboard_obj:
            refresh = dashboard_obj["refresh"]
            if not isinstance(refresh, str):
                return False, "Dashboard refresh must be a string"
            if len(refresh) > 50:
                return False, "Dashboard refresh string is too long"
        
        # Validate tags if present
        if "tags" in dashboard_obj:
            tags = dashboard_obj["tags"]
            if not isinstance(tags, list):
                return False, "Dashboard tags must be an array"
            if len(tags) > 50:
                return False, "Dashboard cannot have more than 50 tags"
            for tag in tags:
                if not isinstance(tag, str):
                    return False, "Dashboard tags must be strings"
                if len(tag) > 50:
                    return False, "Dashboard tag is too long"
        
        return True, None
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def sanitize_dashboard_json(dashboard_json: str) -> str:
    """
    Sanitize dashboard JSON to prevent injection attacks.
    
    Args:
        dashboard_json: JSON string to sanitize
        
    Returns:
        Sanitized JSON string
        
    Raises:
        SanitizationError: If sanitization fails
    """
    try:
        # Parse and re-serialize to ensure clean JSON
        dashboard_data = json.loads(dashboard_json)
        
        # Remove any null bytes or control characters from strings
        dashboard_data = _remove_control_characters(dashboard_data)
        
        # Re-serialize with sorting to ensure consistency
        sanitized_json = json.dumps(dashboard_data, sort_keys=True, ensure_ascii=False)
        
        return sanitized_json
        
    except json.JSONDecodeError as e:
        raise SanitizationError(f"Failed to parse JSON for sanitization: {str(e)}")
    except Exception as e:
        raise SanitizationError(f"Sanitization error: {str(e)}")


def _remove_control_characters(data: Any) -> Any:
    """
    Recursively remove control characters from strings in data structures.
    
    Args:
        data: Data structure to clean
        
    Returns:
        Cleaned data structure
    """
    if isinstance(data, dict):
        return {key: _remove_control_characters(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_remove_control_characters(item) for item in data]
    elif isinstance(data, str):
        # Remove null bytes and other problematic control characters
        # Keep tabs, newlines, and carriage returns
        cleaned = ''.join(char for char in data if ord(char) >= 32 or char in '\t\n\r')
        return cleaned
    else:
        return data


def validate_configmap_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate ConfigMap name conforms to Kubernetes naming conventions.
    
    Args:
        name: ConfigMap name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "ConfigMap name cannot be empty"
    
    if len(name) > 253:
        return False, "ConfigMap name cannot exceed 253 characters"
    
    if not K8S_NAME_PATTERN.match(name):
        return False, "ConfigMap name must conform to RFC 1123 subdomain format"
    
    return True, None


def validate_namespace(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate namespace name conforms to Kubernetes naming conventions.
    
    Args:
        name: Namespace name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Namespace name cannot be empty"
    
    if len(name) > 63:
        return False, "Namespace name cannot exceed 63 characters"
    
    if not K8S_NAME_PATTERN.match(name):
        return False, "Namespace name must conform to RFC 1123 subdomain format"
    
    return True, None


def validate_labels(labels: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validate Kubernetes labels.
    
    Args:
        labels: Dictionary of labels to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(labels, dict):
        return False, "Labels must be a dictionary"
    
    for key, value in labels.items():
        # Validate key
        if not isinstance(key, str):
            return False, f"Label key must be a string: {key}"
        
        if len(key) > 63:
            return False, f"Label key exceeds 63 characters: {key}"
        
        if not K8S_LABEL_KEY_PATTERN.match(key):
            return False, f"Invalid label key format: {key}"
        
        # Validate value
        if not isinstance(value, str):
            return False, f"Label value must be a string: {value}"
        
        if len(value) > 63:
            return False, f"Label value exceeds 63 characters: {value}"
        
        if not K8S_LABEL_VALUE_PATTERN.match(value):
            return False, f"Invalid label value format: {value}"
    
    return True, None


def validate_annotations(annotations: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validate Kubernetes annotations.
    
    Args:
        annotations: Dictionary of annotations to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(annotations, dict):
        return False, "Annotations must be a dictionary"
    
    for key, value in annotations.items():
        # Validate key
        if not isinstance(key, str):
            return False, f"Annotation key must be a string: {key}"
        
        if len(key) > 253:
            return False, f"Annotation key exceeds 253 characters: {key}"
        
        if not K8S_ANNOTATION_KEY_PATTERN.match(key):
            return False, f"Invalid annotation key format: {key}"
        
        # Validate value
        if not isinstance(value, str):
            return False, f"Annotation value must be a string: {value}"
        
        # Annotations can be longer than labels (up to 256KB total)
        if len(value) > 256000:
            return False, f"Annotation value exceeds 256KB: {key}"
    
    return True, None


def validate_folder_name(folder: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Grafana folder name.
    
    Args:
        folder: Folder name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not folder:
        return False, "Folder name cannot be empty"
    
    if len(folder) > 100:
        return False, "Folder name cannot exceed 100 characters"
    
    if not FOLDER_NAME_PATTERN.match(folder):
        return False, "Folder name contains invalid characters"
    
    return True, None


def validate_configmap_data(configmap_data: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validate ConfigMap data section.
    
    Args:
        configmap_data: Dictionary of ConfigMap data entries
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not configmap_data:
        return False, "ConfigMap data cannot be empty"
    
    if not isinstance(configmap_data, dict):
        return False, "ConfigMap data must be a dictionary"
    
    # Check size limits
    total_size = sum(len(value) for value in configmap_data.values())
    if total_size > 1 * 1024 * 1024:  # 1MB limit
        return False, f"ConfigMap data exceeds 1MB limit (current: {total_size} bytes)"
    
    # Validate each key-value pair
    for key, value in configmap_data.items():
        # Validate key
        if not isinstance(key, str):
            return False, f"ConfigMap data key must be a string: {key}"
        
        if len(key) > 253:
            return False, f"ConfigMap data key exceeds 253 characters: {key}"
        
        # Validate value
        if not isinstance(value, str):
            return False, f"ConfigMap data value must be a string: {key}"
        
        # Check for suspicious patterns in values
        if _contains_suspicious_patterns(value):
            logger.warning(f"Suspicious pattern detected in ConfigMap data key '{key}'")
    
    return True, None


def _contains_suspicious_patterns(text: str) -> bool:
    """
    Check for suspicious patterns that might indicate injection attempts.
    
    Note: This does NOT flag Grafana template variables like ${var} which are expected.
    
    Args:
        text: Text to check
        
    Returns:
        True if suspicious patterns found
    """
    # Patterns to check for:
    # - Script tags
    # - Event handlers
    # - JavaScript protocol
    # - Shell command injections
    
    suspicious_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'[\;\|\&\`]',  # Shell command separators
        # Note: We don't flag ${...} as it's normal for Grafana template variables
        # Only flag if it's clearly malicious: ${__import__('os').system('...')}
        r'\$\{__import__',  # Python import attempts in template strings
        r'\$\{java\.lang',  # Java class loading attempts
        r'\$\{request\.',  # Servlet request access
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string to prevent injection attacks.
    
    Args:
        text: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        raise SanitizationError("Input must be a string")
    
    # Remove control characters except common whitespace
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
    
    # Truncate if necessary
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_and_sanitize_dashboard_entry(key: str, value: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate and sanitize a single dashboard entry from ConfigMap data.
    
    Args:
        key: ConfigMap data key
        value: ConfigMap data value (JSON string)
        
    Returns:
        Tuple of (is_valid, error_message, sanitized_value)
    """
    # Validate key
    if not key.endswith('.json'):
        return False, f"Dashboard key must end with '.json': {key}", None
    
    # Validate dashboard JSON
    is_valid, error = validate_dashboard_json(value)
    if not is_valid:
        return False, error, None
    
    # Sanitize dashboard JSON
    try:
        sanitized_value = sanitize_dashboard_json(value)
        return True, None, sanitized_value
    except SanitizationError as e:
        return False, str(e), None


def validate_configmap_complete(configmap) -> Tuple[bool, Optional[str]]:
    """
    Complete validation of a ConfigMap object before processing.
    
    Args:
        configmap: Kubernetes ConfigMap object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Validate metadata
        if not hasattr(configmap, 'metadata') or not configmap.metadata:
            return False, "ConfigMap missing metadata"
        
        # Validate name
        name = configmap.metadata.name
        is_valid, error = validate_configmap_name(name)
        if not is_valid:
            return False, f"Invalid ConfigMap name: {error}"
        
        # Validate namespace
        namespace = configmap.metadata.namespace
        is_valid, error = validate_namespace(namespace)
        if not is_valid:
            return False, f"Invalid namespace: {error}"
        
        # Validate labels
        if hasattr(configmap.metadata, 'labels') and configmap.metadata.labels:
            is_valid, error = validate_labels(configmap.metadata.labels)
            if not is_valid:
                return False, f"Invalid labels: {error}"
        
        # Validate annotations
        if hasattr(configmap.metadata, 'annotations') and configmap.metadata.annotations:
            is_valid, error = validate_annotations(configmap.metadata.annotations)
            if not is_valid:
                return False, f"Invalid annotations: {error}"
        
        # Validate data
        if not hasattr(configmap, 'data') or not configmap.data:
            return False, "ConfigMap missing data section"
        
        is_valid, error = validate_configmap_data(configmap.data)
        if not is_valid:
            return False, f"Invalid ConfigMap data: {error}"
        
        # Validate folder label if present
        if hasattr(configmap.metadata, 'labels') and configmap.metadata.labels:
            folder = configmap.metadata.labels.get('grafana_folder')
            if folder:
                is_valid, error = validate_folder_name(folder)
                if not is_valid:
                    return False, f"Invalid folder name: {error}"
        
        return True, None
        
    except Exception as e:
        return False, f"ConfigMap validation error: {str(e)}"

