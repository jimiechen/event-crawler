import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { NativeMessagingHost } from '../native-messaging-host';
import { v4 as uuidv4 } from 'uuid';
import { HTTP_STATUS } from '../constant';
// @ts-ignore
import { WebSocket } from 'ws'; // Provided by @types/ws or implicit

/**
 * Controller for direct communication between Playwright and Chrome Extension
 * Bypasses MCP protocol for stability and simplicity
 */
export class DirectController {
  private nativeHost: NativeMessagingHost;
  // Store login requests status: requestId -> { status: 'pending' | 'completed' | 'failed', data?: any }
  private requestStore: Map<string, { status: string; data?: any; timestamp: number }> = new Map();
  
  // Store WebSocket clients
  private wsClients: Set<WebSocket> = new Set();
  
  // Store SSE clients (response objects)
  private sseClients: Set<FastifyReply> = new Set();

  constructor(nativeHost: NativeMessagingHost) {
    this.nativeHost = nativeHost;
    // Cleanup old requests periodically
    setInterval(() => this.cleanupOldRequests(), 60000);
  }

  public registerRoutes(fastify: FastifyInstance) {
    // 1. Playwright initiates a login request
    fastify.post('/api/login-request', async (request: FastifyRequest<{ Body: { url: string } }>, reply: FastifyReply) => {
      const { url } = request.body;
      if (!url) {
        return reply.status(HTTP_STATUS.BAD_REQUEST).send({ error: 'URL is required' });
      }

      const requestId = uuidv4();
      
      // Store initial status
      this.requestStore.set(requestId, {
        status: 'pending',
        timestamp: Date.now()
      });

      try {
        // Send message to Chrome Extension via Native Host
        // Note: We don't wait for the full login flow here, just the acknowledgement that the extension received the request
        this.nativeHost.sendMessage({
          type: 'LOGIN_REQUEST',
          payload: { url, requestId }
        });

        return reply.status(HTTP_STATUS.OK).send({ 
          requestId, 
          status: 'pending',
          message: 'Login request sent to Chrome Extension' 
        });
      } catch (error: any) {
        return reply.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).send({ 
          error: `Failed to send message to extension: ${error.message}` 
        });
      }
    });

    // 2. Playwright polls for login status
    fastify.get('/api/login-status/:requestId', async (request: FastifyRequest<{ Params: { requestId: string } }>, reply: FastifyReply) => {
      const { requestId } = request.params;
      const requestData = this.requestStore.get(requestId);

      if (!requestData) {
        return reply.status(HTTP_STATUS.BAD_REQUEST).send({ error: 'Request ID not found' });
      }

      return reply.status(HTTP_STATUS.OK).send(requestData);
    });

    // 3. WebSocket endpoint for bidirectional communication
    fastify.get('/api/ws', { websocket: true } as any, ((connection: any, req: FastifyRequest) => {
      const socket = connection.socket as WebSocket;
      this.wsClients.add(socket);
      
      console.log('[DirectController] WebSocket client connected');

      socket.on('message', (message: any) => {
        try {
           const msg = JSON.parse(message.toString());
           console.log('[DirectController] Received message from WebSocket:', msg);
           
           // Forward to Chrome Extension if needed
           if (msg.target === 'extension') {
             this.nativeHost.sendMessage(msg.payload);
           }
        } catch (err) {
           console.error('[DirectController] Error parsing WebSocket message:', err);
        }
      });

      socket.on('close', () => {
        this.wsClients.delete(socket);
        console.log('[DirectController] WebSocket client disconnected');
      });
      
      socket.on('error', (err: Error) => {
         console.error('[DirectController] WebSocket error:', err);
         this.wsClients.delete(socket);
      });
    }) as any);

    // 4. SSE endpoint for server-sent events
    fastify.get('/api/events', async (req, reply) => {
      reply.raw.setHeader('Content-Type', 'text/event-stream');
      reply.raw.setHeader('Cache-Control', 'no-cache');
      reply.raw.setHeader('Connection', 'keep-alive');
      reply.raw.flushHeaders();

      this.sseClients.add(reply);
      console.log('[DirectController] SSE client connected');

      // Send initial heartbeat
      reply.raw.write('event: connected\ndata: {}\n\n');

      req.raw.on('close', () => {
        this.sseClients.delete(reply);
        console.log('[DirectController] SSE client disconnected');
      });
    });
  }

  /**
   * Broadcast message to all connected clients (WebSocket and SSE)
   */
  private broadcast(type: string, payload: any) {
     const message = JSON.stringify({ type, payload });
     
     // Broadcast to WebSockets
     for (const client of this.wsClients) {
       if (client.readyState === 1) { // OPEN
         client.send(message);
       }
     }

     // Broadcast to SSE
     for (const client of this.sseClients) {
        client.raw.write(`event: ${type}\ndata: ${JSON.stringify(payload)}\n\n`);
     }
  }

  /**
   * Called by NativeMessagingHost when a message is received from Chrome Extension
   */
  public handleExtensionMessage(message: any) {
    // Broadcast all extension messages to connected clients
    this.broadcast('EXTENSION_MESSAGE', message);

    if (message.type === 'LOGIN_COMPLETED' && message.requestId) {
      const { requestId, cookies, localStorage } = message.payload;
      if (this.requestStore.has(requestId)) {
        this.requestStore.set(requestId, {
          status: 'completed',
          data: { cookies, localStorage },
          timestamp: Date.now()
        });
        console.log(`[DirectController] Login completed for request ${requestId}`);
      }
    } else if (message.type === 'LOGIN_FAILED' && message.requestId) {
      const { requestId, error } = message.payload;
      if (this.requestStore.has(requestId)) {
        this.requestStore.set(requestId, {
          status: 'failed',
          data: { error },
          timestamp: Date.now()
        });
        console.log(`[DirectController] Login failed for request ${requestId}: ${error}`);
      }
    }
  }

  private cleanupOldRequests() {
    const now = Date.now();
    const TTL = 5 * 60 * 1000; // 5 minutes
    for (const [key, value] of this.requestStore.entries()) {
      if (now - value.timestamp > TTL) {
        this.requestStore.delete(key);
      }
    }
  }
}
