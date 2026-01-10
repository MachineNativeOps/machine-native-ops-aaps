#!/bin/bash
# Root Initialization Script 03 - Governance Initialization
# Machine Native Ops Root Layer Initialization
# Version: 1.0.0

set -e

echo "🏛️  [03-governance-init] Initializing governance..."

# Validate environment
if [ "${MACHINENATIVEOPS_ROOT_INITIALIZED}" != "true" ]; then
    echo "❌ [03-governance-init] ERROR: Root environment not initialized"
    exit 1
fi

# Load governance configuration
GOVERNANCE_CONFIG="${MACHINENATIVEOPS_ROOT}/controlplane/config/root.governance.yaml"

if [ ! -f "${GOVERNANCE_CONFIG}" ]; then
    echo "❌ [03-governance-init] ERROR: Governance config not found"
    exit 1
fi

echo "📋 [03-governance-init] Loading governance configuration..."
echo "   Path: ${GOVERNANCE_CONFIG}"

# Extract governance info
if command -v python3 &> /dev/null; then
    ROLE_COUNT=$(python3 -c "
import yaml
with open('${GOVERNANCE_CONFIG}', 'r') as f:
    data = yaml.safe_load(f)
    print(len(data.get('spec', {}).get('roles', [])))
")
    POLICY_COUNT=$(python3 -c "
import yaml
with open('${GOVERNANCE_CONFIG}', 'r') as f:
    data = yaml.safe_load(f)
    print(len(data.get('spec', {}).get('policies', [])))
")
    echo "   Total roles: ${ROLE_COUNT}"
    echo "   Total policies: ${POLICY_COUNT}"
else
    echo "⚠️  [03-governance-init] WARNING: Cannot extract governance info without Python3"
fi

# Initialize governance registry
GOVERNANCE_REGISTRY="${ROOT_CONFIG_PATH}/.root.jobs/governance-registry.json"

if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import json
import os
from datetime import datetime

governance_config_path = os.environ['GOVERNANCE_CONFIG']
governance_registry_path = os.environ['GOVERNANCE_REGISTRY']

try:
    with open(governance_config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    roles = data.get('spec', {}).get('roles', [])
    policies = data.get('spec', {}).get('policies', [])
    
    registry = {
        "version": "1.0.0",
        "created": datetime.utcnow().isoformat() + 'Z',
        "total_roles": len(roles),
        "total_policies": len(policies),
        "roles": [],
        "policies": []
    }
    
    for role in roles:
        name = role.get('name')
        registry['roles'].append({
            "name": name,
            "description": role.get('description'),
            "permissions": role.get('permissions', []),
            "constraints": role.get('constraints', [])
        })
    
    for policy in policies:
        name = policy.get('name')
        registry['policies'].append({
            "name": name,
            "description": policy.get('description'),
            "rules": policy.get('rules', [])
        })
    
    os.makedirs(os.path.dirname(governance_registry_path), exist_ok=True)
    with open(governance_registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"   ✅ Governance registry initialized")
    print(f"   📊 Total roles: {registry['total_roles']}")
    print(f"   📊 Total policies: {registry['total_policies']}")
    print(f"   📁 Registry: {governance_registry_path}")
    
except Exception as e:
    print(f"   ❌ Error initializing governance registry: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [03-governance-init] ERROR: Governance registry initialization failed"
        exit 1
    fi
else
    echo "⚠️  [03-governance-init] WARNING: Skipping governance registry (Python3 not found)"
fi

echo "✅ [03-governance-init] Governance initialization complete"
echo "   Timestamp: ${MACHINENATIVEOPS_INIT_TIMESTAMP}"
echo ""
