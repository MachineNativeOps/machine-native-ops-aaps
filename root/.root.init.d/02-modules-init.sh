#!/bin/bash
# Root Initialization Script 02 - Modules Initialization
# Machine Native Ops Root Layer Initialization
# Version: 1.0.0

set -e

echo "🔧 [02-modules-init] Initializing modules..."

# Validate environment
if [ "${MACHINENATIVEOPS_ROOT_INITIALIZED}" != "true" ]; then
    echo "❌ [02-modules-init] ERROR: Root environment not initialized"
    exit 1
fi

# Load modules configuration
MODULES_CONFIG="${MACHINENATIVEOPS_ROOT}/controlplane/config/root.modules.yaml"

if [ ! -f "${MODULES_CONFIG}" ]; then
    echo "❌ [02-modules-init] ERROR: Modules config not found"
    exit 1
fi

echo "📋 [02-modules-init] Loading modules configuration..."
echo "   Path: ${MODULES_CONFIG}"

# Extract module count
if command -v python3 &> /dev/null; then
    MODULE_COUNT=$(python3 -c "
import yaml
with open('${MODULES_CONFIG}', 'r') as f:
    data = yaml.safe_load(f)
    print(len(data.get('spec', {}).get('modules', [])))
")
    echo "   Total modules: ${MODULE_COUNT}"
else
    echo "⚠️  [02-modules-init] WARNING: Cannot extract module count without Python3"
fi

# Initialize modules registry
MODULES_REGISTRY="${ROOT_CONFIG_PATH}/.root.jobs/modules-registry.json"

if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import json
import os
from datetime import datetime

modules_config_path = os.environ['MODULES_CONFIG']
modules_registry_path = os.environ['MODULES_REGISTRY']

try:
    with open(modules_config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    modules = data.get('spec', {}).get('modules', [])
    
    registry = {
        "version": "1.0.0",
        "created": datetime.utcnow().isoformat() + 'Z',
        "total_modules": len(modules),
        "enabled_modules": 0,
        "disabled_modules": 0,
        "modules": []
    }
    
    for module in modules:
        name = module.get('name')
        enabled = module.get('enabled', False)
        
        registry['modules'].append({
            "name": name,
            "version": module.get('version'),
            "description": module.get('description'),
            "enabled": enabled,
            "group": module.get('group'),
            "priority": module.get('priority'),
            "dependencies": module.get('dependencies', [])
        })
        
        if enabled:
            registry['enabled_modules'] += 1
        else:
            registry['disabled_modules'] += 1
    
    os.makedirs(os.path.dirname(modules_registry_path), exist_ok=True)
    with open(modules_registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"   ✅ Modules registry initialized")
    print(f"   📊 Total modules: {registry['total_modules']}")
    print(f"   📊 Enabled modules: {registry['enabled_modules']}")
    print(f"   📊 Disabled modules: {registry['disabled_modules']}")
    print(f"   📁 Registry: {modules_registry_path}")
    
except Exception as e:
    print(f"   ❌ Error initializing modules registry: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [02-modules-init] ERROR: Modules registry initialization failed"
        exit 1
    fi
else
    echo "⚠️  [02-modules-init] WARNING: Skipping modules registry (Python3 not found)"
fi

echo "✅ [02-modules-init] Modules initialization complete"
echo "   Timestamp: ${MACHINENATIVEOPS_INIT_TIMESTAMP}"
echo ""
