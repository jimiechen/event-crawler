
import { BACKEND_CONFIG } from './tonghuashun-data-handler';

/**
 * SSE Handler for Real-time Alerts
 */
export function initSSEListener() {
  console.log('Initializing SSE Listener...');

  const sseUrl = `${BACKEND_CONFIG.baseUrl}/api/sse/subscribe`;
  
  // Create EventSource connection
  const eventSource = new EventSource(sseUrl);

  eventSource.onopen = () => {
    console.log('SSE Connection Opened');
  };

  eventSource.onerror = (err) => {
    console.error('SSE Connection Error:', err);
    // Browser will auto-reconnect, but we can log or handle backoff here if needed
  };

  // Listen for 'alert' events
  eventSource.addEventListener('alert', (event: MessageEvent) => {
    try {
      const payload = JSON.parse(event.data);
      console.log('Received Alert:', payload);
      
      // Parse inner data if needed (depends on how backend sends it)
      // Backend sends: data: json.dumps(data)
      // So payload is the data dict
      
      showNotification(payload);
    } catch (e) {
      console.error('Error parsing alert:', e);
    }
  });
}

function showNotification(data: any) {
  const { symbol, name, message, change_percent } = data;
  
  const title = `⚠️ 异动告警: ${name} (${symbol})`;
  const msg = `${message}\n涨幅: ${change_percent}%`;

  chrome.notifications.create({
    type: 'basic',
    iconUrl: chrome.runtime.getURL('icon-128.png'), // Ensure this icon exists
    title: title,
    message: msg,
    priority: 2
  });
}
