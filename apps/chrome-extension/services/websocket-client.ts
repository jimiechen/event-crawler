/**
 * WebSocket Client for MCP Communication
 * Manages connection to Agent WebSocket server
 */

const WS_URL = 'ws://localhost:8765';
const RECONNECT_DELAY = 1000;
const MAX_RECONNECT_ATTEMPTS = 5;
const HEARTBEAT_INTERVAL = 30000;

interface WSMessage {
  messageId: string;
  type: MessageType;
  payload: Uint8Array;
  timestamp: number;
}

enum MessageType {
  UNKNOWN = 0,
  CONNECT = 1,
  CONNECT_ACK = 2,
  HEARTBEAT = 3,
  HEARTBEAT_ACK = 4,
  DISCONNECT = 5,
  SKILL_REQUEST = 10,
  SKILL_RESPONSE = 11,
  SKILL_STREAM = 12,
  BACKEND_REQUEST = 20,
  BACKEND_RESPONSE = 21,
}

interface SkillRequest {
  requestId: string;
  skillName: string;
  platform: string;
  parameters: Record<string, string>;
  imageData?: Uint8Array;
  mimeType?: string;
}

interface SkillResponse {
  requestId: string;
  success: boolean;
  result?: string;
  error?: string;
  processingTimeMs?: number;
}

interface SkillStreamChunk {
  requestId: string;
  chunk: string;
  isComplete: boolean;
  chunkIndex: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private heartbeatTimer: number | null = null;
  private pendingRequests: Map<string, { resolve: (value: SkillResponse) => void; reject: (reason: Error) => void }> = new Map();
  private streamHandlers: Map<string, (chunk: SkillStreamChunk) => void> = new Map();
  private messageListeners: Array<(message: WSMessage) => void> = [];
  private isConnected = false;

  constructor() {
    this.connect();
  }

  /**
   * Establish WebSocket connection
   */
  private connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    console.log('Connecting to WebSocket...');
    this.ws = new WebSocket(WS_URL);
    this.ws.binaryType = 'arraybuffer';

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.sendConnectMessage();
    };

    this.ws.onmessage = (event) => {
      const data = new Uint8Array(event.data as ArrayBuffer);
      const message = this.decodeMessage(data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.isConnected = false;
      this.stopHeartbeat();
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => this.connect(), delay);
  }

  /**
   * Send connect message
   */
  private sendConnectMessage(): void {
    const message: WSMessage = {
      messageId: this.generateId(),
      type: MessageType.CONNECT,
      payload: new TextEncoder().encode(JSON.stringify({
        clientId: this.generateId(),
        clientVersion: '1.0.0',
        capabilities: { streaming: true, imageUpload: true }
      })),
      timestamp: Date.now(),
    };
    this.sendMessage(message);
  }

  /**
   * Start heartbeat
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = window.setInterval(() => {
      const message: WSMessage = {
        messageId: this.generateId(),
        type: MessageType.HEARTBEAT,
        payload: new Uint8Array(),
        timestamp: Date.now(),
      };
      this.sendMessage(message);
    }, HEARTBEAT_INTERVAL);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Send message
   */
  private sendMessage(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const encoded = this.encodeMessage(message);
      this.ws.send(encoded);
    } else {
      console.warn('WebSocket not connected, message queued');
    }
  }

  /**
   * Encode message to binary format
   */
  private encodeMessage(message: WSMessage): Uint8Array {
    const encoder = new TextEncoder();
    const idBytes = encoder.encode(message.messageId);
    const payloadBytes = message.payload;

    // Simple binary format: [type(1)][idLen(1)][id(idLen)][timestamp(8)][payloadLen(4)][payload]
    const buffer = new ArrayBuffer(1 + 1 + idBytes.length + 8 + 4 + payloadBytes.length);
    const view = new DataView(buffer);
    let offset = 0;

    view.setUint8(offset++, message.type);
    view.setUint8(offset++, idBytes.length);
    
    const idArray = new Uint8Array(buffer, offset, idBytes.length);
    idArray.set(idBytes);
    offset += idBytes.length;

    view.setBigInt64(offset, BigInt(message.timestamp));
    offset += 8;

    view.setUint32(offset, payloadBytes.length);
    offset += 4;

    const payloadArray = new Uint8Array(buffer, offset, payloadBytes.length);
    payloadArray.set(payloadBytes);

    return new Uint8Array(buffer);
  }

  /**
   * Decode message from binary format
   */
  private decodeMessage(data: Uint8Array): WSMessage {
    const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
    let offset = 0;

    const type = view.getUint8(offset++);
    const idLen = view.getUint8(offset++);

    const idBytes = new Uint8Array(data.buffer, data.byteOffset + offset, idLen);
    const messageId = new TextDecoder().decode(idBytes);
    offset += idLen;

    const timestamp = Number(view.getBigInt64(offset));
    offset += 8;

    const payloadLen = view.getUint32(offset);
    offset += 4;

    const payload = new Uint8Array(data.buffer, data.byteOffset + offset, payloadLen);

    return { messageId, type, payload, timestamp };
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WSMessage): void {
    // Notify listeners
    this.messageListeners.forEach(listener => listener(message));

    switch (message.type) {
      case MessageType.SKILL_RESPONSE:
        this.handleSkillResponse(message);
        break;
      case MessageType.SKILL_STREAM:
        this.handleSkillStream(message);
        break;
      case MessageType.CONNECT_ACK:
        console.log('Connected to server');
        break;
      case MessageType.HEARTBEAT_ACK:
        // Heartbeat acknowledged
        break;
    }
  }

  /**
   * Handle skill response
   */
  private handleSkillResponse(message: WSMessage): void {
    const response: SkillResponse = JSON.parse(new TextDecoder().decode(message.payload));
    const pending = this.pendingRequests.get(response.requestId);
    if (pending) {
      pending.resolve(response);
      this.pendingRequests.delete(response.requestId);
    }
  }

  /**
   * Handle skill stream
   */
  private handleSkillStream(message: WSMessage): void {
    const chunk: SkillStreamChunk = JSON.parse(new TextDecoder().decode(message.payload));
    const handler = this.streamHandlers.get(chunk.requestId);
    if (handler) {
      handler(chunk);
    }
  }

  /**
   * Call skill
   */
  async callSkill(request: SkillRequest): Promise<SkillResponse> {
    return new Promise((resolve, reject) => {
      this.pendingRequests.set(request.requestId, { resolve, reject });

      const message: WSMessage = {
        messageId: request.requestId,
        type: MessageType.SKILL_REQUEST,
        payload: new TextEncoder().encode(JSON.stringify(request)),
        timestamp: Date.now(),
      };

      this.sendMessage(message);

      // Timeout after 60 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(request.requestId)) {
          this.pendingRequests.delete(request.requestId);
          reject(new Error('Skill call timeout'));
        }
      }, 60000);
    });
  }

  /**
   * Call skill with streaming
   */
  async *callSkillStream(request: SkillRequest): AsyncGenerator<SkillStreamChunk> {
    const chunks: SkillStreamChunk[] = [];
    let isComplete = false;

    this.streamHandlers.set(request.requestId, (chunk) => {
      chunks.push(chunk);
      if (chunk.isComplete) {
        isComplete = true;
      }
    });

    const message: WSMessage = {
      messageId: request.requestId,
      type: MessageType.SKILL_REQUEST,
      payload: new TextEncoder().encode(JSON.stringify({ ...request, stream: true })),
      timestamp: Date.now(),
    };

    this.sendMessage(message);

    while (!isComplete) {
      await this.sleep(100);
      while (chunks.length > 0) {
        yield chunks.shift()!;
      }
    }

    this.streamHandlers.delete(request.requestId);
  }

  /**
   * Add message listener
   */
  addMessageListener(listener: (message: WSMessage) => void): void {
    this.messageListeners.push(listener);
  }

  /**
   * Remove message listener
   */
  removeMessageListener(listener: (message: WSMessage) => void): void {
    const index = this.messageListeners.indexOf(listener);
    if (index > -1) {
      this.messageListeners.splice(index, 1);
    }
  }

  /**
   * Disconnect
   */
  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  /**
   * Check if connected
   */
  get connected(): boolean {
    return this.isConnected;
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Sleep helper
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();
