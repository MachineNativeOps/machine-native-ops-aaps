/**
 * Trace Analyzer - Trace Analysis and Insights
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';
import { Trace, Span } from './trace-manager';

export interface TraceAnalysis {
  traceId: string;
  totalDuration: number;
  spanCount: number;
  criticalPath: Span[];
  bottlenecks: Array<{ span: Span; reason: string }>;
}

export class TraceAnalyzer extends EventEmitter {
  analyze(trace: Trace): TraceAnalysis {
    const criticalPath = this.findCriticalPath(trace.spans);
    const bottlenecks = this.findBottlenecks(trace.spans);
    
    return {
      traceId: trace.traceId,
      totalDuration: trace.duration || 0,
      spanCount: trace.spans.length,
      criticalPath,
      bottlenecks
    };
  }
  
  private findCriticalPath(spans: Span[]): Span[] {
    return spans
      .filter(s => s.duration !== undefined)
      .sort((a, b) => (b.duration || 0) - (a.duration || 0))
      .slice(0, 5);
  }
  
  private findBottlenecks(spans: Span[]): Array<{ span: Span; reason: string }> {
    const bottlenecks: Array<{ span: Span; reason: string }> = [];
    
    for (const span of spans) {
      if (span.duration && span.duration > 1000) {
        bottlenecks.push({
          span,
          reason: `Slow operation: ${span.duration}ms`
        });
      }
    }
    
    return bottlenecks;
  }
}
