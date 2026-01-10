/**
 * Trace Manager - Distributed Tracing Management
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';

export interface Span {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  tags?: Record<string, string>;
  logs?: Array<{ timestamp: number; message: string }>;
}

export interface Trace {
  traceId: string;
  spans: Span[];
  startTime: number;
  endTime?: number;
  duration?: number;
}

export class TraceManager extends EventEmitter {
  private traces: Map<string, Trace>;
  private activeSpans: Map<string, Span>;
  
  constructor() {
    super();
    this.traces = new Map();
    this.activeSpans = new Map();
  }
  
  startTrace(name: string): string {
    const traceId = `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const trace: Trace = {
      traceId,
      spans: [],
      startTime: Date.now()
    };
    
    this.traces.set(traceId, trace);
    
    const rootSpan = this.startSpan(traceId, name);
    
    this.emit('trace:started', { traceId, span: rootSpan });
    
    return traceId;
  }
  
  startSpan(traceId: string, name: string, parentSpanId?: string): Span {
    const span: Span = {
      traceId,
      spanId: `span-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      parentSpanId,
      name,
      startTime: Date.now(),
      tags: {},
      logs: []
    };
    
    this.activeSpans.set(span.spanId, span);
    
    const trace = this.traces.get(traceId);
    if (trace) {
      trace.spans.push(span);
    }
    
    this.emit('span:started', { span });
    
    return span;
  }
  
  endSpan(spanId: string): void {
    const span = this.activeSpans.get(spanId);
    
    if (!span) return;
    
    span.endTime = Date.now();
    span.duration = span.endTime - span.startTime;
    
    this.activeSpans.delete(spanId);
    
    this.emit('span:ended', { span });
    
    // Check if trace is complete
    const trace = this.traces.get(span.traceId);
    if (trace && this.activeSpans.size === 0) {
      trace.endTime = Date.now();
      trace.duration = trace.endTime - trace.startTime;
      this.emit('trace:completed', { trace });
    }
  }
  
  addSpanTag(spanId: string, key: string, value: string): void {
    const span = this.activeSpans.get(spanId);
    if (span && span.tags) {
      span.tags[key] = value;
    }
  }
  
  addSpanLog(spanId: string, message: string): void {
    const span = this.activeSpans.get(spanId);
    if (span && span.logs) {
      span.logs.push({ timestamp: Date.now(), message });
    }
  }
  
  getTrace(traceId: string): Trace | null {
    return this.traces.get(traceId) || null;
  }
  
  getTraces(): Trace[] {
    return Array.from(this.traces.values());
  }
}
