/**
 * Span Collector - Span Collection and Storage
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';
import { Span } from './trace-manager';

export class SpanCollector extends EventEmitter {
  private spans: Span[];
  private maxSpans: number;
  
  constructor(config?: { maxSpans?: number }) {
    super();
    this.spans = [];
    this.maxSpans = config?.maxSpans || 100000;
  }
  
  collect(span: Span): void {
    this.spans.push(span);
    
    if (this.spans.length > this.maxSpans) {
      this.spans.shift();
    }
    
    this.emit('span:collected', { span });
  }
  
  getSpans(traceId?: string): Span[] {
    if (traceId) {
      return this.spans.filter(s => s.traceId === traceId);
    }
    return [...this.spans];
  }
  
  clear(): void {
    this.spans = [];
  }
}
