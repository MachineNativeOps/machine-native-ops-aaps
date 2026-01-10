/**
 * Log Analyzer - Intelligent Log Analysis System
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';
import { LogEntry, LogLevel } from './logger';

export interface LogPattern {
  pattern: RegExp;
  severity: LogLevel;
  description: string;
}

export interface AnalysisResult {
  totalLogs: number;
  errorCount: number;
  warningCount: number;
  patterns: Array<{ pattern: string; count: number }>;
  anomalies: LogEntry[];
}

export class LogAnalyzer extends EventEmitter {
  private patterns: Map<string, LogPattern>;
  
  constructor() {
    super();
    this.patterns = new Map();
  }
  
  registerPattern(name: string, pattern: LogPattern): void {
    this.patterns.set(name, pattern);
  }
  
  analyze(logs: LogEntry[]): AnalysisResult {
    const errorCount = logs.filter(l => l.level >= LogLevel.ERROR).length;
    const warningCount = logs.filter(l => l.level === LogLevel.WARN).length;
    
    const patternMatches = new Map<string, number>();
    const anomalies: LogEntry[] = [];
    
    for (const log of logs) {
      for (const [name, pattern] of this.patterns) {
        if (pattern.pattern.test(log.message)) {
          patternMatches.set(name, (patternMatches.get(name) || 0) + 1);
          
          if (pattern.severity >= LogLevel.ERROR) {
            anomalies.push(log);
          }
        }
      }
    }
    
    return {
      totalLogs: logs.length,
      errorCount,
      warningCount,
      patterns: Array.from(patternMatches.entries()).map(([pattern, count]) => ({
        pattern,
        count
      })),
      anomalies
    };
  }
  
  detectAnomalies(logs: LogEntry[]): LogEntry[] {
    return logs.filter(log => {
      if (log.level >= LogLevel.ERROR) return true;
      
      for (const pattern of this.patterns.values()) {
        if (pattern.pattern.test(log.message) && pattern.severity >= LogLevel.ERROR) {
          return true;
        }
      }
      
      return false;
    });
  }
}
