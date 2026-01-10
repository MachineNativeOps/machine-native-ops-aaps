#!/bin/bash
# Root Initialization Script 04 - Trust Chain Initialization
# Machine Native Ops Root Layer Initialization
# Version: 1.0.0

set -e

echo "🔒 [04-trust-init] Initializing trust chain..."

# Validate environment
if [ "${MACHINENATIVEOPS_ROOT_INITIALIZED}" != "true" ]; then
    echo "❌ [04-trust-init] ERROR: Root environment not initialized"
    exit 1
fi

# Load trust configuration
TRUST_CONFIG="${MACHINENATIVEOPS_ROOT}/controlplane/config/root.trust.yaml"

if [ ! -f "${TRUST_CONFIG}" ]; then
    echo "❌ [04-trust-init] ERROR: Trust config not found"
    exit 1
fi

echo "📋 [04-trust-init] Loading trust configuration..."
echo "   Path: ${TRUST_CONFIG}"

# Create trust directories
TRUST_DIRS=(
    "${ROOT_CONFIG_PATH}/.root.trust"
    "${ROOT_CONFIG_PATH}/.root.trust/certificates"
    "${ROOT_CONFIG_PATH}/.root.trust/keys"
    "${ROOT_CONFIG_PATH}/.root.trust/attestations"
)

for dir in "${TRUST_DIRS[@]}"; do
    if [ ! -d "${dir}" ]; then
        mkdir -p "${dir}"
        echo "   Created: ${dir}"
    fi
done

# Initialize trust registry
TRUST_REGISTRY="${ROOT_CONFIG_PATH}/.root.jobs/trust-registry.json"

if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import json
import os
from datetime import datetime

trust_config_path = os.environ['TRUST_CONFIG']
trust_registry_path = os.environ['TRUST_REGISTRY']

try:
    with open(trust_config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Extract trust information
    trust_chain = data.get('spec', {}).get('trust_chain', {})
    certificates = data.get('spec', {}).get('certificates', [])
    
    registry = {
        "version": "1.0.0",
        "created": datetime.utcnow().isoformat() + 'Z',
        "trust_chain": trust_chain,
        "certificates_count": len(certificates),
        "certificates": []
    }
    
    for cert in certificates:
        name = cert.get('name')
        registry['certificates'].append({
            "name": name,
            "type": cert.get('type'),
            "purpose": cert.get('purpose'),
            "status": cert.get('status', 'active')
        })
    
    os.makedirs(os.path.dirname(trust_registry_path), exist_ok=True)
    with open(trust_registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"   ✅ Trust registry initialized")
    print(f"   📊 Certificates: {registry['certificates_count']}")
    print(f"   📁 Registry: {trust_registry_path}")
    
except Exception as e:
    print(f"   ❌ Error initializing trust registry: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [04-trust-init] ERROR: Trust registry initialization failed"
        exit 1
    fi
else
    echo "⚠️  [04-trust-init] WARNING: Skipping trust registry (Python3 not found)"
fi

echo "✅ [04-trust-init] Trust chain initialization complete"
echo "   Timestamp: ${MACHINENATIVEOPS_INIT_TIMESTAMP}"
echo ""
