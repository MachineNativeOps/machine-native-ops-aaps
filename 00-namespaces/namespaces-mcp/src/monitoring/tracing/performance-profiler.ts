/**
 * Performance Profiler - Detailed Performance Profiling
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';

export interface ProfileEntry {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  cpuTime?: number;
  memoryDelta?: number;
}

export class PerformanceProfiler extends EventEmitter {
  private profiles: Map<string, ProfileEntry>;
  private history: ProfileEntry[];
  
  constructor() {
    super();
    this.profiles = new Map();
    this.history = [];
  }
  
  start(name: string): void {
    const entry: ProfileEntry = {
      name,
      startTime: Date.now()
    };
    
    this.profiles.set(name, entry);
    this.emit('profile:started', { name });
  }
  
  end(name: string): ProfileEntry | null {
    const entry = this.profiles.get(name);
    
    if (!entry) return null;
    
    entry.endTime = Date.now();
    entry.duration = entry.endTime - entry.startTime;
    
    this.profiles.delete(name);
    this.history.push(entry);
    
    this.emit('profile:ended', { entry });
    
    return entry;
  }
  
  getHistory(): ProfileEntry[] {
    return [...this.history];
  }
  
  getStatistics(name: string): {
    count: number;
    avgDuration: number;
    minDuration: number;
    maxDuration: number;
  } {
    const entries = this.history.filter(e => e.name === name && e.duration !== undefined);
    
    if (entries.length === 0) {
      return { count: 0, avgDuration: 0, minDuration: 0, maxDuration: 0 };
    }
    
    const durations = entries.map(e => e.duration!);
    
    return {
      count: entries.length,
      avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations)
    };
  }
}
