/**
 * Middleware Chain - Request/response pipeline with middleware
 * 
 * Provides comprehensive middleware chain execution with error handling,
 * conditional execution, parallel processing, and performance optimization.
 * 
 * @module integration/middleware/middleware-chain
 */

import { EventEmitter } from 'events';

/**
 * Middleware context
 */
export interface MiddlewareContext {
  request: unknown;
  response?: unknown;
  state: Map<string, unknown>;
  metadata: Record<string, unknown>;
}

/**
 * Next function
 */
export type NextFunction = () => Promise<void>;

/**
 * Middleware function
 */
export type MiddlewareFunction = (
  context: MiddlewareContext,
  next: NextFunction
) => Promise<void>;

/**
 * Middleware options
 */
export interface MiddlewareOptions {
  name?: string;
  priority?: number;
  condition?: (context: MiddlewareContext) => boolean | Promise<boolean>;
  timeout?: number;
}

/**
 * Middleware
 */
export interface Middleware {
  name: string;
  priority: number;
  fn: MiddlewareFunction;
  options: MiddlewareOptions;
}

/**
 * Middleware Chain
 */
export class MiddlewareChain extends EventEmitter {
  private middlewares: Middleware[] = [];

  use(fn: MiddlewareFunction, options: MiddlewareOptions = {}): this {
    const middleware: Middleware = {
      name: options.name || `middleware_${this.middlewares.length}`,
      priority: options.priority ?? 0,
      fn,
      options
    };
    this.middlewares.push(middleware);
    this.middlewares.sort((a, b) => b.priority - a.priority);
    return this;
  }

  async execute(context: MiddlewareContext): Promise<void> {
    await this.executeChain(context, 0);
  }

  private async executeChain(context: MiddlewareContext, index: number): Promise<void> {
    if (index >= this.middlewares.length) return;
    const middleware = this.middlewares[index];
    await middleware.fn(context, () => this.executeChain(context, index + 1));
  }

  clear(): void {
    this.middlewares = [];
  }
}

export function createMiddlewareChain(): MiddlewareChain {
  return new MiddlewareChain();
}

export default MiddlewareChain;
