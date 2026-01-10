/**
 * Dashboard Server - Real-Time Monitoring Dashboard
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';

export interface DashboardConfig {
  port?: number;
  refreshInterval?: number;
  enableAuth?: boolean;
}

export class DashboardServer extends EventEmitter {
  private config: Required<DashboardConfig>;
  private clients: Set<any>;
  private running: boolean;
  
  constructor(config?: DashboardConfig) {
    super();
    
    this.config = {
      port: config?.port || 3000,
      refreshInterval: config?.refreshInterval || 5000,
      enableAuth: config?.enableAuth || false
    };
    
    this.clients = new Set();
    this.running = false;
  }
  
  async start(): Promise<void> {
    if (this.running) return;
    
    this.running = true;
    this.emit('server:started', { port: this.config.port });
  }
  
  async stop(): Promise<void> {
    if (!this.running) return;
    
    this.running = false;
    this.clients.clear();
    this.emit('server:stopped');
  }
  
  broadcast(data: any): void {
    for (const client of this.clients) {
      this.sendToClient(client, data);
    }
  }
  
  private sendToClient(client: any, data: any): void {
    this.emit('data:sent', { client, data });
  }
  
  isRunning(): boolean {
    return this.running;
  }
}
