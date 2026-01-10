/**
 * Visualization - Data Visualization Engine
 * 
 * @version 1.0.0
 */

import { EventEmitter } from 'events';

export enum ChartType {
  LINE = 'line',
  BAR = 'bar',
  PIE = 'pie',
  AREA = 'area',
  SCATTER = 'scatter'
}

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    color?: string;
  }>;
}

export interface DashboardChart {
  id: string;
  type: ChartType;
  title: string;
  data: ChartData;
  options?: Record<string, any>;
}

export class Visualization extends EventEmitter {
  private charts: Map<string, DashboardChart>;
  
  constructor() {
    super();
    this.charts = new Map();
  }
  
  createChart(chart: Omit<DashboardChart, 'id'>): string {
    const id = `chart-${crypto.randomUUID()}`;
    
    const fullChart: DashboardChart = {
      ...chart,
      id
    };
    
    this.charts.set(id, fullChart);
    this.emit('chart:created', { chart: fullChart });
    
    return id;
  }
  
  updateChart(id: string, data: ChartData): void {
    const chart = this.charts.get(id);
    
    if (!chart) {
      throw new Error(`Chart ${id} not found`);
    }
    
    chart.data = data;
    this.emit('chart:updated', { chart });
  }
  
  getChart(id: string): DashboardChart | null {
    return this.charts.get(id) || null;
  }
  
  getAllCharts(): DashboardChart[] {
    return Array.from(this.charts.values());
  }
  
  deleteChart(id: string): void {
    this.charts.delete(id);
    this.emit('chart:deleted', { id });
  }
  
  generateTimeSeriesChart(
    title: string,
    data: Array<{ timestamp: number; value: number }>,
    label: string
  ): string {
    const chartData: ChartData = {
      labels: data.map(d => new Date(d.timestamp).toISOString()),
      datasets: [{
        label,
        data: data.map(d => d.value)
      }]
    };
    
    return this.createChart({
      type: ChartType.LINE,
      title,
      data: chartData
    });
  }
}
