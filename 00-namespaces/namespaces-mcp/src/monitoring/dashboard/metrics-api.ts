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
  
  constructor(metricsCollector: MetricsCollector) {
    super();
    this.endpoints = new Map();
    this.metricsCollector = metricsCollector;
    this.registerDefaultEndpoints();
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
  
  async handleRequest(method: string, path: string, params?: any): Promise<any> {
    const key = `${method}:${path}`;
    const endpoint = this.endpoints.get(key);
    
    if (!endpoint) {
      throw new Error(`Endpoint not found: ${key}`);
    }
    
    return endpoint.handler(params || {});
  }
}
