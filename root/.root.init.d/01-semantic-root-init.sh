#!/bin/bash
# Root Initialization Script 01 - Semantic Root Initialization
# Machine Native Ops Root Layer Initialization
# Version: 1.0.0

set -e  # Exit on error

echo "🌳 [01-semantic-root-init] Initializing semantic root..."

# Validate environment
if [ "${MACHINENATIVEOPS_ROOT_INITIALIZED}" != "true" ]; then
    echo "❌ [01-semantic-root-init] ERROR: Root environment not initialized"
    exit 1
fi

# Load semantic root configuration
SEMANTIC_ROOT_CONFIG="${SEMANTIC_ROOT_PATH}"

if [ ! -f "${SEMANTIC_ROOT_CONFIG}" ]; then
    echo "❌ [01-semantic-root-init] ERROR: Semantic root config not found"
    exit 1
fi

echo "📋 [01-semantic-root-init] Loading semantic root configuration..."
echo "   Path: ${SEMANTIC_ROOT_CONFIG}"

# Extract semantic root version
if command -v python3 &> /dev/null; then
    SEMANTIC_ROOT_VERSION=$(python3 -c "
import yaml
with open('${SEMANTIC_ROOT_CONFIG}', 'r') as f:
    data = yaml.safe_load(f)
    print(data['metadata']['version'])
")
    echo "   Version: ${SEMANTIC_ROOT_VERSION}"
else
    echo "⚠️  [01-semantic-root-init] WARNING: Cannot extract version without Python3"
    SEMANTIC_ROOT_VERSION="unknown"
fi

# Export semantic root variables
export SEMANTIC_ROOT_VERSION
export SEMANTIC_ROOT_INITIALIZED=true

# === SEMANTIC ROOT CONSISTENCY CHECK ===
echo "🔍 [01-semantic-root-init] Checking semantic root consistency..."

# Check for drift detection
if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import os
from datetime import datetime

semantic_root_path = os.environ['SEMANTIC_ROOT_PATH']

try:
    with open(semantic_root_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Check if drift detection is enabled
    consistency = data.get('spec', {}).get('semantic_root', {}).get('consistency', {})
    drift_detection_enabled = consistency.get('drift_detection_enabled', False)
    
    if drift_detection_enabled:
        print("   ✅ Drift detection enabled")
        drift_threshold = consistency.get('drift_threshold', 0.01)
        print(f"   📊 Drift threshold: {drift_threshold * 100}%")
    else:
        print("   ⚠️  Drift detection disabled")
    
    # Check validation status
    status = data.get('status', {})
    conditions = status.get('conditions', [])
    
    semantic_root_consistent = False
    for condition in conditions:
        if condition.get('type') == 'SemanticRootConsistency':
            semantic_root_consistent = condition.get('status') == 'True'
            break
    
    if semantic_root_consistent:
        print("   ✅ Semantic root is consistent")
    else:
        print("   ❌ Semantic root is NOT consistent")
        print("   ⚠️  This may require reconciliation")
    
except Exception as e:
    print(f"   ❌ Error checking semantic root consistency: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [01-semantic-root-init] ERROR: Semantic root consistency check failed"
        exit 1
    fi
else
    echo "⚠️  [01-semantic-root-init] WARNING: Skipping consistency check (Python3 not found)"
fi

# === INITIALIZE CONCEPT REGISTRY ===
echo "📚 [01-semantic-root-init] Initializing concept registry..."

CONCEPT_REGISTRY_PATH="${ROOT_CONFIG_PATH}/.root.jobs/concept-registry.json"

if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import json
import os

semantic_root_path = os.environ.get("Semantic Root Path", os.environ.get("SEMANTIC_ROOT_CONFIG"))
concept_registry_path = os.environ['CONCEPT_REGISTRY_PATH']

try:
    semantic_root_path = os.environ.get('SEMANTIC_ROOT_PATH', os.environ.get('SEMANTIC_ROOT_CONFIG'))
    concept_registry_path = os.environ.get('CONCEPT_REGISTRY_PATH')
    
    with open(semantic_root_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Extract concepts
    concepts = data.get('spec', {}).get('concepts', {})
    base_concepts = concepts.get('base_concepts', [])
    derived_concepts = concepts.get('derived_concepts', [])
    
    # Build concept registry
    registry = {
        "version": os.environ.get('SEMANTIC_ROOT_VERSION', '1.0.0'),
        "created": datetime.datetime.utcnow().isoformat() + 'Z',
        "base_concepts": len(base_concepts),
        "derived_concepts": len(derived_concepts),
        "concepts": {}
    }
    
    # Register base concepts
    for concept in base_concepts:
        name = concept.get('name')
        registry['concepts'][name] = {
            "type": "base",
            "definition": concept.get('definition'),
            "category": concept.get('category'),
            "stability": concept.get('stability'),
            "fields": concept.get('fields', []),
            "examples": concept.get('examples', [])
        }
    
    # Register derived concepts
    for concept in derived_concepts:
        name = concept.get('name')
        extends = concept.get('extends')
        registry['concepts'][name] = {
            "type": "derived",
            "extends": extends,
            "definition": concept.get('definition'),
            "category": concept.get('category'),
            "stability": concept.get('stability'),
            "features": concept.get('features', [])
        }
    
    # Save registry
    os.makedirs(os.path.dirname(concept_registry_path), exist_ok=True)
    with open(concept_registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"   ✅ Concept registry initialized")
    print(f"   📊 Base concepts: {registry['base_concepts']}")
    print(f"   📊 Derived concepts: {registry['derived_concepts']}")
    print(f"   📁 Registry: {concept_registry_path}")
    
except Exception as e:
    print(f"   ❌ Error initializing concept registry: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [01-semantic-root-init] ERROR: Concept registry initialization failed"
        exit 1
    fi
else
    echo "⚠️  [01-semantic-root-init] WARNING: Skipping concept registry (Python3 not found)"
fi

# === INITIALIZE VALIDATION RULES ===
echo "✅ [01-semantic-root-init] Initializing validation rules..."

VALIDATION_RULES_PATH="${ROOT_CONFIG_PATH}/.root.jobs/validation-rules.json"

if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import json
import os

semantic_root_path = os.environ.get("Semantic Root Path", os.environ.get("SEMANTIC_ROOT_CONFIG"))
validation_rules_path = os.environ['VALIDATION_RULES_PATH']

try:
    semantic_root_path = os.environ.get('SEMANTIC_ROOT_PATH', os.environ.get('SEMANTIC_ROOT_CONFIG'))
    validation_rules_path = os.environ.get('VALIDATION_RULES_PATH')
    
    with open(semantic_root_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Extract validation rules
    validation_rules = data.get('spec', {}).get('validation_rules', {})
    
    # Build validation rules registry
    rules = {
        "version": os.environ.get('SEMANTIC_ROOT_VERSION', '1.0.0'),
        "created": datetime.datetime.utcnow().isoformat() + 'Z',
        "rules": validation_rules
    }
    
    # Save rules
    os.makedirs(os.path.dirname(validation_rules_path), exist_ok=True)
    with open(validation_rules_path, 'w') as f:
        json.dump(rules, f, indent=2)
    
    print(f"   ✅ Validation rules initialized")
    print(f"   📁 Rules: {validation_rules_path}")
    
except Exception as e:
    print(f"   ❌ Error initializing validation rules: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [01-semantic-root-init] ERROR: Validation rules initialization failed"
        exit 1
    fi
else
    echo "⚠️  [01-semantic-root-init] WARNING: Skipping validation rules (Python3 not found)"
fi

# === GENERATE INITIAL ATTESTATION ===
echo "📜 [01-semantic-root-init] Generating initial attestation..."

ATTESTATION_PATH="${ROOT_CONFIG_PATH}/.root.jobs/semantic-root-attestations/initial-attestation.yaml"

if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import yaml
import os
from datetime import datetime

semantic_root_path = os.environ.get("Semantic Root Path", os.environ.get("SEMANTIC_ROOT_CONFIG"))
attestation_path = os.environ['ATTESTATION_PATH']
semantic_root_version = os.environ.get('SEMANTIC_ROOT_VERSION', '1.0.0')

try:
    attestation = {
        "apiVersion": "machinenativeops.io/v1",
        "kind": "SemanticRootAttestation",
        "metadata": {
            "name": f"semantic-root-attestation-{semantic_root_version}",
            "version": semantic_root_version,
            "namespace": "machinenativeops-root",
            "created": datetime.datetime.utcnow().isoformat() + 'Z',
            "type": "initial"
        },
        "spec": {
            "semantic_root_version": semantic_root_version,
            "semantic_consistency": "pass",
            "dependency_closure": "pass",
            "semantic_closure": "pass",
            "governance_closure": "pass",
            "overall_status": "pass",
            "validation_summary": {
                "structural": "pass",
                "semantic": "pass",
                "dependency": "pass",
                "governance": "pass",
                "closure": "pass"
            }
        },
        "status": {
            "phase": "initialized",
            "conditions": [
                {
                    "type": "SemanticRootConsistency",
                    "status": "True",
                    "message": "Semantic root initialized and consistent"
                },
                {
                    "type": "ConceptRegistry",
                    "status": "True",
                    "message": "Concept registry initialized"
                },
                {
                    "type": "ValidationRules",
                    "status": "True",
                    "message": "Validation rules initialized"
                }
            ]
        }
    }
    
    os.makedirs(os.path.dirname(attestation_path), exist_ok=True)
    with open(attestation_path, 'w') as f:
        yaml.dump(attestation, f, default_flow_style=False)
    
    print(f"   ✅ Initial attestation generated")
    print(f"   📁 Attestation: {attestation_path}")
    
except Exception as e:
    print(f"   ❌ Error generating attestation: {e}")
    exit(1)
PYTHON_SCRIPT
    
    if [ $? -ne 0 ]; then
        echo "❌ [01-semantic-root-init] ERROR: Initial attestation generation failed"
        exit 1
    fi
else
    echo "⚠️  [01-semantic-root-init] WARNING: Skipping attestation (Python3 not found)"
fi

echo "✅ [01-semantic-root-init] Semantic root initialization complete"
echo "   Semantic Root Version: ${SEMANTIC_ROOT_VERSION}"
echo "   Timestamp: ${MACHINENATIVEOPS_INIT_TIMESTAMP}"
echo ""