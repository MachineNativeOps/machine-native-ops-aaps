export interface EnhancedValidationDimension {
  dimension: string;
  accuracy?: number;
  techniques?: string[];
  dimensions?: number;
  coverage?: number;
  standards?: string[];
  technologies?: string[];
  prediction_accuracy?: number;
  horizon?: string;
}

export interface PerformanceTargets {
  validationSpeed: string;
  falsePositiveRate: number;
  falseNegativeRate: number;
  coverage: number;
}

export interface ImplementationRequirements {
  quantumHardware: string;
  aiAcceleration: string;
  blockchainIntegration: string;
  realTimeMonitoring: string;
  automatedRemediation: string;
}

export interface WorldClassValidation {
  apiVersion: "validation.machinenativeops/v1";
  kind: "WorldClassValidation";
  metadata: {
    name: string;
    description?: string;
  };
  spec: {
    enhancedValidationDimensions: EnhancedValidationDimension[];
    performanceTargets: PerformanceTargets;
    implementationRequirements: ImplementationRequirements;
  };
}

export const manifestPath = "workspace/config/validation/world-class-validation.yaml";
export const schemaPath = "workspace/config/validation/schemas/world-class-validation.schema.json";
