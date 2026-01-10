#!/bin/bash
# Root Initialization Script 06 - Integrity Initialization
# Machine Native Ops Root Layer Initialization
# Version: 1.0.0

set -e

echo "🛡️  [06-integrity-init] Initializing integrity..."

# Validate environment
if [ "${MACHINENATIVEOPS_ROOT_INITIALIZED}" != "true" ]; then
    echo "❌ [06-integrity-init] ERROR: Root environment not initialized"
    exit 1
fi

# Load integrity configuration
INTEGRITY_CONFIG="${MACHINENATIVEOPS_ROOT}/controlplane/config/root.integrity.yaml"

if [ ! -f "${INTEGRITY_CONFIG}" ]; then
    echo "❌ [06-integrity-init] ERROR: Integrity config not found"
    exit 1
fi

echo "📋 [06-integrity-init] Loading integrity configuration..."
echo "   Path: ${INTEGRITY_CONFIG}"

# Initialize integrity registry
INTEGRITY_REGISTRY="${ROOT_CONFIG_PATH}/.root.jobs/integrity-registry.json"

if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import json
import os
import hashlib
from datetime import datetime

integrity_config_path = os.environ['INTEGRITY_CONFIG']
integrity_registry_path = os.environ['INTEGRITY_REGISTRY']

try:
    with open(integrity_config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Extract integrity information
    hash_lock = data.get('spec', {}).get('hash_lock', {})
    drift_detection = data.get('spec', {}).get('drift_detection', {})
    
    # Calculate hash of integrity config
    with open(integrity_config_path, 'rb') as f:
        config_hash = hashlib.sha256(f.read()).hexdigest()
    
    registry = {
        "version": "1.0.0",
        "created": datetime.utcnow().isoformat() + 'Z',
        "integrity_config_hash": config_hash,
        "hash_lock": hash_lock,
        "drift_detection": drift_detection,
        "drift_threshold": drift_detection.get('threshold', 0.01),
        "monitored_artifacts": 0
    }
    
    os.makedirs(os.path.dirname(integrity_registry_path), exist_ok=True)
    with open(integrity_registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"   ✅ Integrity registry initialized")
    print(f"   🔒 Config hash: {config_hash[:16]}...")
    print(f"   📊 Drift threshold: {registry['drift_threshold'] * 100}%")
    print(f"   📁 Registry: {integrity_registry_path}")
    
except Exception as e:
    print(f"   ❌ Error initializing integrity registry: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [06-integrity-init] ERROR: Integrity registry initialization failed"
        exit 1
    fi
else
    echo "⚠️  [06-integrity-init] WARNING: Skipping integrity registry (Python3 not found)"
fi

echo "✅ [06-integrity-init] Integrity initialization complete"
echo "   Timestamp: ${MACHINENATIVEOPS_INIT_TIMESTAMP}"
echo ""
