/**
 * Audit Logger - Security and Compliance Audit Logging
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';

export enum AuditEventType {
  USER_LOGIN = 'user_login',
  USER_LOGOUT = 'user_logout',
  DATA_ACCESS = 'data_access',
  DATA_MODIFICATION = 'data_modification',
  PERMISSION_CHANGE = 'permission_change',
  SYSTEM_CONFIG_CHANGE = 'system_config_change'
}

export interface AuditEvent {
  id: string;
  type: AuditEventType;
  timestamp: number;
  userId?: string;
  action: string;
  resource?: string;
  result: 'success' | 'failure';
  metadata?: Record<string, any>;
  ipAddress?: string;
}

export class AuditLogger extends EventEmitter {
  private events: AuditEvent[];
  private maxEvents: number;
  
  constructor(config?: { maxEvents?: number }) {
    super();
    this.events = [];
    this.maxEvents = config?.maxEvents || 100000;
  }
  
  log(event: Omit<AuditEvent, 'id' | 'timestamp'>): void {
    const auditEvent: AuditEvent = {
      ...event,
      id: `audit-${crypto.randomUUID()}`,
      timestamp: Date.now()
    };
    
    this.events.push(auditEvent);
    
    if (this.events.length > this.maxEvents) {
      this.events.shift();
    }
    
    this.emit('audit:logged', { event: auditEvent });
  }
  
  getEvents(options?: {
    type?: AuditEventType;
    userId?: string;
    startTime?: number;
    endTime?: number;
    result?: 'success' | 'failure';
  }): AuditEvent[] {
    let events = [...this.events];
    
    if (options?.type) {
      events = events.filter(e => e.type === options.type);
    }
    
    if (options?.userId) {
      events = events.filter(e => e.userId === options.userId);
    }
    
    if (options?.startTime) {
      events = events.filter(e => e.timestamp >= options.startTime!);
    }
    
    if (options?.endTime) {
      events = events.filter(e => e.timestamp <= options.endTime!);
    }
    
    if (options?.result) {
      events = events.filter(e => e.result === options.result);
    }
    
    return events;
  }
  
  exportAuditTrail(startTime: number, endTime: number): string {
    const events = this.getEvents({ startTime, endTime });
    return JSON.stringify(events, null, 2);
  }
}
