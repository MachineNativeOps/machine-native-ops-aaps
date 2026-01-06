"""
Unified pipeline manifest loader v3.0.0 (MCP integration).

INSTANT Execution Architecture:
- AI auto-evolution, instant delivery, zero latency
- Execution standard: <3 minutes full stack, 0 human intervention
- Competitiveness: Replit | Claude | GPT equivalent

Artifacts:
- Manifest: workspace/mcp/pipelines/unified-pipeline-config.yaml
- Schema:   workspace/mcp/schemas/unified-pipeline.schema.json
- TS types: workspace/mcp/types/unifiedPipeline.ts
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
import logging
from typing import Any, Dict, List, Literal, Optional

# Configure logging for pipeline loader
logger = logging.getLogger(__name__)

import yaml


MANIFEST_PATH = Path("workspace/mcp/pipelines/unified-pipeline-config.yaml")
SCHEMA_PATH = Path("workspace/mcp/schemas/unified-pipeline.schema.json")


# ========================================
# INSTANT Execution Constants
# ========================================
class InstantExecutionStandards:
    """Runtime constants for INSTANT execution mode validation.

    Note on schema vs runtime constraints:
    - The JSON schema allows maxParallelAgents up to 1024 to support future
      scaling and non-INSTANT pipeline modes (Standard, Hybrid).
    - For INSTANT-Autonomous mode, the runtime maximum is 256 agents.
    - The schema's higher maximum provides flexibility for infrastructure
      that may scale beyond current INSTANT requirements while maintaining
      backward compatibility.
    """

    MAX_LATENCY_INSTANT = 100       # ms
    MAX_LATENCY_FAST = 500          # ms
    MAX_LATENCY_STANDARD = 5000     # ms
    MAX_STAGE_LATENCY = 30000       # ms
    MAX_TOTAL_LATENCY = 180000      # ms (3 minutes)
    MIN_PARALLEL_AGENTS = 64
    MAX_PARALLEL_AGENTS = 256       # Runtime max for INSTANT mode (schema allows 1024)
    HUMAN_INTERVENTION = 0
    SUCCESS_RATE_FEATURE = 95       # %
    SUCCESS_RATE_FIX = 90           # %
    SUCCESS_RATE_OPTIMIZE = 85      # %


AGENT_TYPES = [
    "analyzer",
    "generator",
    "validator",
    "deployer",
    "sentinel",
    "diagnostic",
    "fixer",
    "optimizer",
    "architect",
    "tester",
]


# ========================================
# Event-Driven Configuration
# ========================================
@dataclass
class EventDrivenConfig:
    mode: str
    closedLoop: bool
    maxConcurrentEvents: int
    eventQueueSize: int


@dataclass
class InputUnification:
    protocols: List[str]
    normalization: str
    validation: str
    timeout: int
    eventDriven: Optional[EventDrivenConfig] = None


# ========================================
# Auto-Scaling Configuration
# ========================================
@dataclass
class ScalingMetric:
    name: str
    target: float
    scaleUpThreshold: Optional[float] = None
    scaleDownThreshold: Optional[float] = None


@dataclass
class AutoScalingConfig:
    enabled: bool
    scaleFactor: float
    cooldownSeconds: int
    metrics: List[ScalingMetric] = field(default_factory=list)


@dataclass
class CoreScheduling:
    maxParallelAgents: int
    taskDecomposition: str
    resourceArbitration: str
    loadBalancing: str
    syncBarrier: str
    minParallelAgents: Optional[int] = None
    autoScaling: Optional[AutoScalingConfig] = None


# ========================================
# Latency Thresholds
# ========================================
@dataclass
class LatencyThresholds:
    instant: int
    fast: int
    standard: int
    maxStage: int
    maxTotal: int


# ========================================
# Pipeline Entries
# ========================================
@dataclass
class PipelineEntry:
    name: str
    type: str
    entrypoint: Optional[str] = None
    worldClassValidationRef: Optional[str] = None
    policies: Optional[str] = None
    manifests: Optional[str] = None
    dashboards: Optional[str] = None
    latency: Optional[int] = None
    parallelism: Optional[int] = None
    priority: Optional[str] = None
    capabilities: Optional[List[str]] = None


# ========================================
# INSTANT Pipelines
# ========================================
@dataclass
class InstantPipelineStage:
    name: str
    agent: str
    latency: int
    parallelism: int


@dataclass
class InstantPipeline:
    """INSTANT Pipeline requires zero human intervention.

    The humanIntervention field must always be 0 for INSTANT-Autonomous mode
    pipelines. This is enforced both at the type level (Literal[0]) and at
    runtime via __post_init__ validation.
    """

    name: str
    totalLatencyTarget: int
    humanIntervention: Literal[0]
    successRateTarget: float
    stages: List[InstantPipelineStage]
    description: Optional[str] = None

    def __post_init__(self) -> None:
        # Defensive runtime validation for cases where type checking is bypassed
        # (e.g., dynamic data loading from YAML, JSON deserialization, or direct
        # dict unpacking). The Literal[0] type annotation provides static type
        # checking, but this ensures runtime safety as well.
        if self.humanIntervention != 0:
            raise ValueError(
                f"InstantPipeline.humanIntervention must be 0 for INSTANT pipelines, "
                f"got {self.humanIntervention!r}"
            )


# ========================================
# MCP Integration
# ========================================
@dataclass
class ToolAdapter:
    name: str
    path: str
    capabilities: Optional[List[str]] = None


@dataclass
class McpIntegration:
    serverRef: str
    toolAdapters: List[ToolAdapter]
    realTimeSync: str
    crossPlatformCoordination: Optional[str] = None


# ========================================
# Outputs
# ========================================
@dataclass
class Outputs:
    auditLog: str
    evidenceChain: str
    statusReport: str
    autoRemediation: str
    notifications: str


# ========================================
# Auto-Healing
# ========================================
@dataclass
class HealingStrategy:
    name: str
    conditions: Dict[str, Any]
    actions: List[str]
    maxRetries: Optional[int] = None
    backoffMultiplier: Optional[float] = None


@dataclass
class AutoHealing:
    enabled: bool
    strategies: List[HealingStrategy] = field(default_factory=list)


# ========================================
# Governance Validation
# ========================================
@dataclass
class GovernanceValidationRule:
    """Governance validation rule configuration.

    The implementationStatus field indicates whether the validator script is
    currently implemented or planned for future development. This helps
    distinguish between active validators and aspirational configuration.
    """

    standard: str
    validator: str
    checkInterval: int
    criteria: List[str]
    failureAction: str
    implementationStatus: Optional[str] = None  # "implemented" or "planned"


# ========================================
# Metadata
# ========================================
@dataclass
class PipelineLabels:
    """Pipeline metadata labels.

    Note: The TypeScript interface allows arbitrary additional properties via
    index signatures ([key: string]: string | undefined), but this Python
    dataclass is more restrictive and only accepts the defined fields.
    Unknown fields will be filtered out with a warning during construction.
    To handle arbitrary labels, consider using a TypedDict or Dict[str, str].
    """

    tier: Optional[str] = None
    evolution: Optional[str] = None
    humanIntervention: Optional[str] = None


@dataclass
class PipelineAnnotations:
    """Pipeline metadata annotations.

    Note: The TypeScript interface allows arbitrary additional properties via
    index signatures ([key: string]: string | undefined), but this Python
    dataclass is more restrictive and only accepts the defined fields.
    Unknown fields will be filtered out with a warning during construction.
    To handle arbitrary annotations, consider using a TypedDict or Dict[str, str].
    """

    philosophy: Optional[str] = None
    competitiveness: Optional[str] = None
    standard: Optional[str] = None


@dataclass
class PipelineMetadata:
    name: str
    version: str
    mode: str
    labels: Optional[PipelineLabels] = None
    annotations: Optional[PipelineAnnotations] = None


# ========================================
# Unified Pipeline Spec
# ========================================
@dataclass
class UnifiedPipelineSpec:
    inputUnification: InputUnification
    coreScheduling: CoreScheduling
    pipelines: List[PipelineEntry]
    mcpIntegration: McpIntegration
    outputs: Outputs
    latencyThresholds: Optional[LatencyThresholds] = None
    instantPipelines: Optional[List[InstantPipeline]] = None
    autoHealing: Optional[AutoHealing] = None
    governanceValidation: Optional[List[GovernanceValidationRule]] = None


# ========================================
# Main Manifest
# ========================================
@dataclass
class UnifiedPipelineManifest:
    apiVersion: str
    kind: str
    metadata: PipelineMetadata
    spec: UnifiedPipelineSpec


def load_manifest(path: Path = MANIFEST_PATH) -> UnifiedPipelineManifest:
    """Load YAML manifest into typed dataclasses with validation."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    # Validate top-level keys
    for key in ("apiVersion", "kind", "metadata", "spec"):
        if key not in data:
            raise ValueError(f"Missing required top-level key: {key}")

    spec = data["spec"]

    # Validate required spec sections
    for section in ("inputUnification", "coreScheduling", "mcpIntegration", "outputs"):
        if section not in spec:
            raise ValueError(f"Missing required spec section: {section}")

    # Parse pipelines
    pipelines_data = spec.get("pipelines", [])
    if not isinstance(pipelines_data, list):
        raise ValueError("spec.pipelines must be a list")
    pipelines = [_safe_construct(PipelineEntry, p, "pipelines[*]") for p in pipelines_data]

    # Parse instant pipelines (v3)
    instant_pipelines = None
    if "instantPipelines" in spec:
        instant_pipelines_data = spec["instantPipelines"]
        if not isinstance(instant_pipelines_data, list):
            raise ValueError("spec.instantPipelines must be a list")
        instant_pipelines = []
        for ip in instant_pipelines_data:
            stages = [_safe_construct(InstantPipelineStage, s, "instantPipelines[*].stages[*]") for s in ip.get("stages", [])]
            instant_pipelines.append(InstantPipeline(
                name=ip["name"],
                description=ip.get("description"),
                totalLatencyTarget=ip["totalLatencyTarget"],
                humanIntervention=ip["humanIntervention"],
                successRateTarget=ip["successRateTarget"],
                stages=stages,
            ))

    # Parse tool adapters
    adapters_data = spec["mcpIntegration"].get("toolAdapters", [])
    if not isinstance(adapters_data, list):
        raise ValueError("spec.mcpIntegration.toolAdapters must be a list")
    adapters = [_safe_construct(ToolAdapter, t, "mcpIntegration.toolAdapters[*]") for t in adapters_data]

    # Parse auto-scaling
    auto_scaling = None
    if "autoScaling" in spec.get("coreScheduling", {}):
        as_data = spec["coreScheduling"]["autoScaling"]
        metrics = [_safe_construct(ScalingMetric, m, "coreScheduling.autoScaling.metrics[*]") for m in as_data.get("metrics", [])]
        auto_scaling = AutoScalingConfig(
            enabled=as_data.get("enabled", False),
            scaleFactor=as_data.get("scaleFactor", 1.0),
            cooldownSeconds=as_data.get("cooldownSeconds", 30),
            metrics=metrics,
        )

    # Parse event-driven config
    event_driven = None
    if "eventDriven" in spec.get("inputUnification", {}):
        ed_data = spec["inputUnification"]["eventDriven"]
        event_driven = _safe_construct(EventDrivenConfig, ed_data, "inputUnification.eventDriven")

    # Parse latency thresholds
    latency_thresholds = None
    if "latencyThresholds" in spec:
        latency_thresholds = _safe_construct(LatencyThresholds, spec["latencyThresholds"], "latencyThresholds")

    # Parse auto-healing
    auto_healing = None
    if "autoHealing" in spec:
        ah_data = spec["autoHealing"]
        strategies = [_safe_construct(HealingStrategy, s, "autoHealing.strategies[*]") for s in ah_data.get("strategies", [])]
        auto_healing = AutoHealing(
            enabled=ah_data.get("enabled", False),
            strategies=strategies,
        )

    # Parse governance validation
    governance_validation = None
    if "governanceValidation" in spec:
        gv_data = spec["governanceValidation"]
        if isinstance(gv_data, list):
            governance_validation = [_safe_construct(GovernanceValidationRule, g, "governanceValidation[*]") for g in gv_data]

    # Parse metadata
    meta_data = data["metadata"]
    labels = None
    if "labels" in meta_data:
        labels = _safe_construct(PipelineLabels, meta_data["labels"], "metadata.labels")
    annotations = None
    if "annotations" in meta_data:
        annotations = _safe_construct(PipelineAnnotations, meta_data["annotations"], "metadata.annotations")

    metadata = PipelineMetadata(
        name=meta_data["name"],
        version=meta_data["version"],
        mode=meta_data["mode"],
        labels=labels,
        annotations=annotations,
    )

    # Build input unification
    iu_data = spec["inputUnification"]
    input_unification = InputUnification(
        protocols=iu_data["protocols"],
        normalization=iu_data["normalization"],
        validation=iu_data["validation"],
        timeout=iu_data["timeout"],
        eventDriven=event_driven,
    )

    # Build core scheduling
    cs_data = spec["coreScheduling"]
    core_scheduling = CoreScheduling(
        maxParallelAgents=cs_data["maxParallelAgents"],
        minParallelAgents=cs_data.get("minParallelAgents"),
        taskDecomposition=cs_data["taskDecomposition"],
        resourceArbitration=cs_data["resourceArbitration"],
        loadBalancing=cs_data["loadBalancing"],
        syncBarrier=cs_data["syncBarrier"],
        autoScaling=auto_scaling,
    )

    # Build MCP integration
    mcp_data = spec["mcpIntegration"]
    mcp_integration = McpIntegration(
        serverRef=mcp_data["serverRef"],
        toolAdapters=adapters,
        realTimeSync=mcp_data["realTimeSync"],
        crossPlatformCoordination=mcp_data.get("crossPlatformCoordination"),
    )

    return UnifiedPipelineManifest(
        apiVersion=data["apiVersion"],
        kind=data["kind"],
        metadata=metadata,
        spec=UnifiedPipelineSpec(
            inputUnification=input_unification,
            coreScheduling=core_scheduling,
            latencyThresholds=latency_thresholds,
            pipelines=pipelines,
            instantPipelines=instant_pipelines,
            mcpIntegration=mcp_integration,
            outputs=_safe_construct(Outputs, spec["outputs"], "outputs"),
            autoHealing=auto_healing,
            governanceValidation=governance_validation,
        ),
    )


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    """Load JSON Schema for validation tooling."""
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_construct(cls, data: dict, label: str):
    """Safely construct a dataclass, filtering out unknown fields.

    Note: This function filters out fields not defined in the dataclass to allow
    forward compatibility when new fields are added to YAML configs. A warning
    is logged when fields are filtered to help detect potential typos in config.
    """
    if data is None:
        raise ValueError(f"Cannot construct {label}: data is None")

    # Get valid field names for this dataclass
    valid_fields = {f.name for f in cls.__dataclass_fields__.values()}

    # Filter data to only include valid fields and log filtered ones
    filtered_data = {}
    unknown_fields = []
    for k, v in data.items():
        if k in valid_fields:
            filtered_data[k] = v
        else:
            unknown_fields.append(k)

    if unknown_fields:
        logger.warning(
            "Ignoring unknown fields in %s for %s: %s. "
            "These may be typos or fields from a newer config version.",
            label,
            cls.__name__,
            unknown_fields,
        )

    try:
        return cls(**filtered_data)
    except (TypeError, KeyError, ValueError) as exc:
        raise ValueError(f"Failed constructing {label} for {cls.__name__}: {exc}") from exc


# ========================================
# Validation Helpers
# ========================================
def is_instant_mode(manifest: UnifiedPipelineManifest) -> bool:
    """Check if the pipeline is in INSTANT-Autonomous mode."""
    return manifest.metadata.mode == "INSTANT-Autonomous"


def has_zero_human_intervention(manifest: UnifiedPipelineManifest) -> bool:
    """Check if the pipeline has zero human intervention."""
    if manifest.metadata.labels:
        return manifest.metadata.labels.humanIntervention == "0"
    return False


def is_v3_pipeline(manifest: UnifiedPipelineManifest) -> bool:
    """Check if the pipeline uses v3 API."""
    return manifest.apiVersion == "pipeline.machinenativeops/v3"


def validate_latency_compliance(manifest: UnifiedPipelineManifest) -> bool:
    """Validate that configured latency thresholds comply with INSTANT standards.

    This function validates that the manifest's latency thresholds are configured
    to be equal to or stricter than the INSTANT execution standards. A threshold
    is compliant if it's at or below the corresponding standard maximum.

    For example:
    - If standard MAX_LATENCY_INSTANT is 100ms, a config with instant=50ms passes
    - If standard MAX_LATENCY_INSTANT is 100ms, a config with instant=150ms fails

    The intent is to ensure that no pipeline is configured with latency thresholds
    that are more permissive than what INSTANT execution mode requires.

    Args:
        manifest: The loaded pipeline manifest to validate.

    Returns:
        True if all latency thresholds comply with INSTANT standards,
        or True if no latency thresholds are configured.
    """
    if not manifest.spec.latencyThresholds:
        return True

    thresholds = manifest.spec.latencyThresholds
    return (
        thresholds.instant <= InstantExecutionStandards.MAX_LATENCY_INSTANT
        and thresholds.fast <= InstantExecutionStandards.MAX_LATENCY_FAST
        and thresholds.standard <= InstantExecutionStandards.MAX_LATENCY_STANDARD
        and thresholds.maxStage <= InstantExecutionStandards.MAX_STAGE_LATENCY
        and thresholds.maxTotal <= InstantExecutionStandards.MAX_TOTAL_LATENCY
    )


def validate_parallelism(manifest: UnifiedPipelineManifest) -> bool:
    """Validate that parallelism is within INSTANT execution standards.

    Validates both maxParallelAgents and minParallelAgents (if configured)
    against the INSTANT execution standards.

    Args:
        manifest: The loaded pipeline manifest to validate.

    Returns:
        True if parallelism settings comply with INSTANT standards.
    """
    scheduling = manifest.spec.coreScheduling
    standards = InstantExecutionStandards

    # Validate maxParallelAgents is within allowed INSTANT range
    if not (standards.MIN_PARALLEL_AGENTS <= scheduling.maxParallelAgents <= standards.MAX_PARALLEL_AGENTS):
        return False

    # Validate minParallelAgents in INSTANT mode (if configured)
    if is_instant_mode(manifest) and scheduling.minParallelAgents is not None:
        if scheduling.minParallelAgents < standards.MIN_PARALLEL_AGENTS:
            return False

    return True


__all__ = [
    # Main functions
    "load_manifest",
    "load_schema",
    # Validation helpers
    "is_instant_mode",
    "has_zero_human_intervention",
    "is_v3_pipeline",
    "validate_latency_compliance",
    "validate_parallelism",
    # Constants
    "InstantExecutionStandards",
    "AGENT_TYPES",
    # Main manifest
    "UnifiedPipelineManifest",
    "UnifiedPipelineSpec",
    "PipelineMetadata",
    # Input/Scheduling
    "InputUnification",
    "EventDrivenConfig",
    "CoreScheduling",
    "AutoScalingConfig",
    "ScalingMetric",
    "LatencyThresholds",
    # Pipelines
    "PipelineEntry",
    "InstantPipeline",
    "InstantPipelineStage",
    # MCP
    "McpIntegration",
    "ToolAdapter",
    # Outputs
    "Outputs",
    # Auto-Healing
    "AutoHealing",
    "HealingStrategy",
    # Governance
    "GovernanceValidationRule",
]
