export interface InputUnification {
  protocols: string[];
  normalization: string;
  validation: string;
  timeout: string | number;
}

export interface CoreScheduling {
  maxParallelAgents: number;
  taskDecomposition: string;
  resourceArbitration: string;
  loadBalancing: string;
  syncBarrier: string;
}

export interface PipelineEntry {
  name: string;
  type: string;
  entrypoint?: string;
  worldClassValidationRef?: string;
  policies?: string;
  manifests?: string;
  dashboards?: string;
}

export interface ToolAdapter {
  name: string;
  path: string;
}

export interface McpIntegration {
  serverRef: string;
  toolAdapters: ToolAdapter[];
  realTimeSync: string;
}

export interface Outputs {
  auditLog: string;
  evidenceChain: string;
  statusReport: string;
  autoRemediation: string;
  notifications: string;
}

export interface UnifiedPipeline {
  apiVersion: "pipeline.machinenativeops/v2";
  kind: "UnifiedPipeline";
  metadata: {
    name: string;
    version: string;
    mode: string;
  };
  spec: {
    inputUnification: InputUnification;
    coreScheduling: CoreScheduling;
    pipelines: PipelineEntry[];
    mcpIntegration: McpIntegration;
    outputs: Outputs;
  };
}

export const unifiedPipelineManifestPath = "workspace/mcp/pipelines/unified-pipeline-config.yaml";
export const unifiedPipelineSchemaPath = "workspace/mcp/schemas/unified-pipeline.schema.json";
