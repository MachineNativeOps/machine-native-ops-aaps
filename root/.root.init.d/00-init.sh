#!/bin/bash
# Root Initialization Script 00 - Basic Environment Setup
# Machine Native Ops Root Layer Initialization
# Version: 1.0.0

set -e  # Exit on error

echo "🚀 [00-init] Starting root layer initialization..."

# === ENVIRONMENT SETUP ===
echo "📋 [00-init] Setting up environment..."

# Set basic environment variables
export MACHINENATIVEOPS_ROOT="${MACHINENATIVEOPS_ROOT:-/workspace/machine-native-ops}"
export MACHINENATIVEOPS_VERSION="${MACHINENATIVEOPS_VERSION:-1.0.0}"
export BOOT_MODE="${BOOT_MODE:-production}"

# Set paths
export CONTROLPLANE_PATH="${CONTROLPLANE_PATH:-${MACHINENATIVEOPS_ROOT}/controlplane}"
export ROOT_CONFIG_PATH="${MACHINENATIVEOPS_ROOT}/root"
export SEMANTIC_ROOT_PATH="${ROOT_CONFIG_PATH}/.root.semantic-root.yaml"

# Validate basic paths
if [ ! -d "${MACHINENATIVEOPS_ROOT}" ]; then
    echo "❌ [00-init] ERROR: MachineNativeOps root directory not found: ${MACHINENATIVEOPS_ROOT}"
    exit 1
fi

if [ ! -d "${CONTROLPLANE_PATH}" ]; then
    echo "❌ [00-init] ERROR: Controlplane directory not found: ${CONTROLPLANE_PATH}"
    exit 1
fi

if [ ! -f "${SEMANTIC_ROOT_PATH}" ]; then
    echo "❌ [00-init] ERROR: Semantic root configuration not found: ${SEMANTIC_ROOT_PATH}"
    exit 1
fi

echo "✅ [00-init] Environment setup complete"
echo "   - Root: ${MACHINENATIVEOPS_ROOT}"
echo "   - Controlplane: ${CONTROLPLANE_PATH}"
echo "   - Semantic Root: ${SEMANTIC_ROOT_PATH}"

# === VALIDATE SEMANTIC ROOT ===
echo "🔍 [00-init] Validating semantic root..."

if command -v python3 &> /dev/null; then
    # Use Python to validate YAML structure
    python3 -c "
import yaml
import sys
try:
    with open('${SEMANTIC_ROOT_PATH}', 'r') as f:
        data = yaml.safe_load(f)
        if 'metadata' in data and 'spec' in data and 'status' in data:
            print('✅ Semantic root structure valid')
            sys.exit(0)
        else:
            print('❌ Semantic root missing required sections')
            sys.exit(1)
except Exception as e:
    print(f'❌ Error validating semantic root: {e}')
    sys.exit(1)
"
    if [ $? -ne 0 ]; then
        echo "❌ [00-init] ERROR: Semantic root validation failed"
        exit 1
    fi
else
    echo "⚠️  [00-init] WARNING: Python3 not found, skipping semantic root validation"
fi

# === CREATE DIRECTORIES ===
echo "📁 [00-init] Creating required directories..."

directories=(
    "${MACHINENATIVEOPS_ROOT}/root/.root.jobs"
    "${MACHINENATIVEOPS_ROOT}/root/.root.jobs/attestations"
    "${MACHINENATIVEOPS_ROOT}/root/.root.jobs/gate-locks"
    "${MACHINENATIVEOPS_ROOT}/root/.root.jobs/semantic-root-attestations"
    "${MACHINENATIVEOPS_ROOT}/root/.root.jobs/backup"
    "${MACHINENATIVEOPS_ROOT}/var/log/machinenativenops"
    "${MACHINENATIVEOPS_ROOT}/tmp/machinenativenops"
)

for dir in "${directories[@]}"; do
    if [ ! -d "${dir}" ]; then
        mkdir -p "${dir}"
        echo "   Created: ${dir}"
    fi
done

echo "✅ [00-init] Directories created"

# === CHECK REQUIRED TOOLS ===
echo "🔧 [00-init] Checking required tools..."

required_tools=("cat" "grep" "sed" "awk" "find")
optional_tools=("python3" "git")

for tool in "${required_tools[@]}"; do
    if command -v "${tool}" &> /dev/null; then
        echo "   ✅ ${tool}"
    else
        echo "   ❌ ${tool} (required)"
        exit 1
    fi
done

for tool in "${optional_tools[@]}"; do
    if command -v "${tool}" &> /dev/null; then
        echo "   ✅ ${tool}"
    else
        echo "   ⚠️  ${tool} (optional, not found)"
    fi
done

echo "✅ [00-init] Tools check complete"

# === SET PERMISSIONS ===
echo "🔒 [00-init] Setting permissions..."

chmod 755 "${MACHINENATIVEOPS_ROOT}/root/.root.init.d"/*.sh 2>/dev/null || true
chmod 755 "${MACHINENATIVEOPS_ROOT}/root/.root.jobs" 2>/dev/null || true

echo "✅ [00-init] Permissions set"

# === EXPORT VARIABLES FOR SUBSEQUENT SCRIPTS ===
export MACHINENATIVEOPS_ROOT_INITIALIZED=true
export MACHINENATIVEOPS_INIT_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "✅ [00-init] Root layer initialization complete"
echo "   Timestamp: ${MACHINENATIVEOPS_INIT_TIMESTAMP}"
echo ""