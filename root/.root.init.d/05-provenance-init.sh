#!/bin/bash
# Root Initialization Script 05 - Provenance Initialization
# Machine Native Ops Root Layer Initialization
# Version: 1.0.0

set -e

echo "📜 [05-provenance-init] Initializing provenance..."

# Validate environment
if [ "${MACHINENATIVEOPS_ROOT_INITIALIZED}" != "true" ]; then
    echo "❌ [05-provenance-init] ERROR: Root environment not initialized"
    exit 1
fi

# Load provenance configuration
PROVENANCE_CONFIG="${MACHINENATIVEOPS_ROOT}/controlplane/config/root.provenance.yaml"

if [ ! -f "${PROVENANCE_CONFIG}" ]; then
    echo "❌ [05-provenance-init] ERROR: Provenance config not found"
    exit 1
fi

echo "📋 [05-provenance-init] Loading provenance configuration..."
echo "   Path: ${PROVENANCE_CONFIG}"

# Initialize provenance registry
PROVENANCE_REGISTRY="${ROOT_CONFIG_PATH}/.root.jobs/provenance-registry.json"

if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import json
import os
from datetime import datetime

provenance_config_path = os.environ['PROVENANCE_CONFIG']
provenance_registry_path = os.environ['PROVENANCE_REGISTRY']

try:
    with open(provenance_config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Extract provenance information
    source_tracking = data.get('spec', {}).get('source_tracking', {})
    modification_history = data.get('spec', {}).get('modification_history', {})
    
    registry = {
        "version": "1.0.0",
        "created": datetime.utcnow().isoformat() + 'Z',
        "source_tracking": source_tracking,
        "modification_history": modification_history,
        "artifacts_tracked": 0
    }
    
    os.makedirs(os.path.dirname(provenance_registry_path), exist_ok=True)
    with open(provenance_registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"   ✅ Provenance registry initialized")
    print(f"   📁 Registry: {provenance_registry_path}")
    
except Exception as e:
    print(f"   ❌ Error initializing provenance registry: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [05-provenance-init] ERROR: Provenance registry initialization failed"
        exit 1
    fi
else
    echo "⚠️  [05-provenance-init] WARNING: Skipping provenance registry (Python3 not found)"
fi

echo "✅ [05-provenance-init] Provenance initialization complete"
echo "   Timestamp: ${MACHINENATIVEOPS_INIT_TIMESTAMP}"
echo ""
