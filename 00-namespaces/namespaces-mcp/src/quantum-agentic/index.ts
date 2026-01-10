/**
 * Quantum-Agentic Intelligence Layer
 * Module 5A - Phase 5 Implementation
 * 
 * Exports all quantum-agentic components for next-generation AI capabilities
 */

// Main System
export {
  QuantumAgenticSystem,
  QuantumAgenticSystemFactory,
  QuantumAgenticConfig,
  SystemStatus,
  ComponentStatus,
  SystemPerformance
} from './quantum-agentic-system';

// Quantum Neural Engine
export {
  QuantumNeuralEngine,
  QuantumNeuralEngineFactory,
  QuantumCircuitConfig,
  QuantumGateType,
  QuantumGate,
  QuantumState,
  Complex,
  QuantumMeasurement,
  QuantumEngineConfig
} from './quantum/quantum-neural-engine';

// Agentic Orchestration
export {
  AgenticOrchestrator,
  AgenticOrchestratorFactory,
  AgentType,
  AgentState,
  AgentConfig,
  Agent,
  Task,
  AgentPerformance,
  NegotiationProtocol,
  Proposal,
  Agreement,
  OrchestratorConfig
} from './agents/agentic-orchestrator';

// Cognitive Reasoning
export {
  CognitiveReasoningEngine,
  CognitiveReasoningEngineFactory,
  ReasoningType,
  ReasoningContext,
  Fact,
  Rule,
  Condition,
  Conclusion,
  Goal,
  Constraint,
  Knowledge,
  Concept,
  Relationship,
  ReasoningResult,
  Alternative,
  ReasoningEngineConfig
} from './reasoning/cognitive-reasoning-engine';

// Multi-Modal Processing
export {
  MultiModalProcessor,
  MultiModalProcessorFactory,
  ModalityType,
  ProcessingRequest,
  Operation,
  ProcessingOptions,
  ProcessingResult,
  ResultMetadata,
  ProcessorConfig
} from './multimodal/multimodal-processor';

// Knowledge Graph
export {
  KnowledgeGraph,
  KnowledgeGraphFactory,
  KnowledgeNode,
  NodeMetadata,
  KnowledgeEdge,
  GraphQuery,
  QueryCriteria,
  QueryOptions,
  GraphPattern,
  PatternNode,
  PatternEdge,
  QueryResult,
  Path,
  GraphConfig
} from './knowledge/knowledge-graph';

/**
 * Quick Start Helper
 */
export function createQuantumAgenticSystem(): QuantumAgenticSystem {
  return QuantumAgenticSystemFactory.createDefault();
}

/**
 * Module Information
 */
export const MODULE_INFO = {
  name: 'Quantum-Agentic Intelligence Layer',
  version: '5.0.0-alpha',
  phase: 'Phase 5 - Module 5A',
  description: 'Next-generation AI with quantum-enhanced reasoning and autonomous agents',
  performanceTargets: {
    quantumOperations: '<1ms',
    agentCoordination: '<100ms',
    reasoningTime: '<500ms',
    multimodalProcessing: '<2s',
    knowledgeQueries: '<50ms'
  },
  capabilities: [
    'Quantum-enhanced neural processing',
    'Multi-agent coordination and negotiation',
    'Advanced cognitive reasoning',
    'Cross-modal understanding',
    'Dynamic knowledge graph management'
  ]
};

export default {
  QuantumAgenticSystem,
  QuantumAgenticSystemFactory,
  createQuantumAgenticSystem,
  MODULE_INFO
};