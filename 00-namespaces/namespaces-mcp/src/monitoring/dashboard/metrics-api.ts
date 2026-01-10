/**
 * Metrics API - RESTful Metrics API
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';
import { MetricsCollector } from '../metrics/metrics-collector';

export interface APIEndpoint {
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  handler: (params: any) => Promise<any>;
}

export class MetricsAPI extends EventEmitter {
  private endpoints: Map<string, APIEndpoint>;
  private metricsCollector: MetricsCollector;
  
  constructor(
    metricsCollector: MetricsCollector,
    options?: {
      registerDefaultEndpoints?: boolean;
    }
  ) {
    super();
    this.endpoints = new Map();
    this.metricsCollector = metricsCollector;
    if (options?.registerDefaultEndpoints ?? true) {
      this.registerDefaultEndpoints();
    }
  }
  
  private registerDefaultEndpoints(): void {
    this.registerEndpoint({
      path: '/metrics',
      method: 'GET',
      handler: async () => {
        return {
          metrics: this.metricsCollector.getMetricNames(),
          statistics: this.metricsCollector.getStatistics()
        };
      }
    });
    
    this.registerEndpoint({
      path: '/metrics/:name',
      method: 'GET',
      handler: async (params) => {
        const metrics = this.metricsCollector.getMetrics(params.name);
        const stats = this.metricsCollector.calculateStatistics(params.name);
        return { metrics, statistics: stats };
      }
    });
    
    this.registerEndpoint({
      path: '/metrics/export/prometheus',
      method: 'GET',
      handler: async () => {
        return this.metricsCollector.exportPrometheus();
      }
    });
  }
  
  registerEndpoint(endpoint: APIEndpoint): void {
    const key = `${endpoint.method}:${endpoint.path}`;
    this.endpoints.set(key, endpoint);
  }
  
  /**
   * Handle incoming API request with path parameter extraction
   */
  async handleRequest(method: string, path: string, params?: any): Promise<any> {
    // Try exact match first
    const exactKey = `${method}:${path}`;
    let endpoint = this.endpoints.get(exactKey);
    
    if (endpoint) {
      return endpoint.handler(params || {});
    }
    
    // Try to match parameterized routes
    for (const [key, ep] of this.endpoints) {
      const [epMethod, epPath] = key.split(':');
      
      if (epMethod !== method) continue;
      
      const pathParams = this.extractPathParams(epPath, path);
      if (pathParams !== null) {
        // Merge path params with query params
        const mergedParams = { ...(params || {}), ...pathParams };
        return ep.handler(mergedParams);
      }
    }
    
    throw new Error(`Endpoint not found: ${method}:${path}`);
  }

  /**
   * Extract path parameters from a parameterized route
   * Returns null if path doesn't match pattern
   */
  private extractPathParams(pattern: string, path: string): Record<string, string> | null {
    const patternParts = pattern.split('/');
    const pathParts = path.split('/');
    
    if (patternParts.length !== pathParts.length) {
      return null;
    }
    
    const params: Record<string, string> = {};
    
    for (let i = 0; i < patternParts.length; i++) {
      const patternPart = patternParts[i];
      const pathPart = pathParts[i];
      
      if (patternPart.startsWith(':')) {
        // This is a parameter
        const paramName = patternPart.slice(1);
        params[paramName] = pathPart;
      } else if (patternPart !== pathPart) {
        // Static part doesn't match
        return null;
      }
    }
    
    return params;
  }
}
