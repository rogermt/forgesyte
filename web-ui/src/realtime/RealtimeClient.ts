/**
 * Phase 10: Real-Time WebSocket Client.
 *
 * TODO: Implement the following:
 * - connect(): Establish WebSocket connection
 * - disconnect(): Close WebSocket connection
 * - send(): Send message to server
 * - on(): Register event handlers
 * - Auto-reconnect with exponential backoff
 * - State machine for connection states (IDLE, CONNECTING, CONNECTED, DISCONNECTED, RECONNECTING, CLOSED)
 *
 * Author: Roger
 * Phase: 10
 */

export enum ConnectionState {
  IDLE = 'IDLE',
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  RECONNECTING = 'RECONNECTING',
  CLOSED = 'CLOSED',
}

export interface RealtimeMessage {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export type MessageHandler = (message: RealtimeMessage) => void;

export class RealtimeClient {
  private url: string;
  private ws: WebSocket | null = null;
  private state: ConnectionState = ConnectionState.IDLE;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelays: number[] = [1000, 2000, 4000, 8000, 16000]; // ms
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  constructor(url: string) {
    this.url = url;
  }

  getState(): ConnectionState {
    return this.state;
  }

  isConnected(): boolean {
    return this.state === ConnectionState.CONNECTED;
  }

  async connect(): Promise<void> {
    if (this.state !== ConnectionState.IDLE && this.state !== ConnectionState.DISCONNECTED) {
      return;
    }

    this.state = ConnectionState.CONNECTING;

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.state = ConnectionState.CONNECTED;
          this.reconnectAttempts = 0;
          this.emit({ type: 'connected', payload: {}, timestamp: new Date().toISOString() });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data) as RealtimeMessage;
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        };

        this.ws.onclose = () => {
          this.state = ConnectionState.DISCONNECTED;
          this.emit({ type: 'disconnected', payload: {}, timestamp: new Date().toISOString() });
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        this.state = ConnectionState.CLOSED;
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.state = ConnectionState.CLOSED;
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.state = ConnectionState.CLOSED;
      return;
    }

    this.state = ConnectionState.RECONNECTING;
    const delay = this.reconnectDelays[this.reconnectAttempts] || 16000;

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect().catch(() => {
        // Reconnect failed, will try again
      });
    }, delay);
  }

  send(type: string, payload: Record<string, unknown>): void {
    if (this.ws && this.state === ConnectionState.CONNECTED) {
      this.ws.send(JSON.stringify({
        type,
        payload,
        timestamp: new Date().toISOString(),
      }));
    }
  }

  on(messageType: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(messageType) || [];
    handlers.push(handler);
    this.messageHandlers.set(messageType, handlers);
  }

  off(messageType: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(messageType) || [];
    const index = handlers.indexOf(handler);
    if (index !== -1) {
      handlers.splice(index, 1);
      this.messageHandlers.set(messageType, handlers);
    }
  }

  private handleMessage(message: RealtimeMessage): void {
    this.emit(message);
  }

  private emit(message: RealtimeMessage): void {
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => handler(message));

    // Also call wildcard handlers
    const wildcardHandlers = this.messageHandlers.get('*') || [];
    wildcardHandlers.forEach(handler => handler(message));
  }
}

