import { okoooMainCrawler } from './okooo-main-crawler';
import { okoooListCrawler } from './okooo-list-crawler';
import { okoooHandicapCrawler } from './okooo-handicap-crawler';

export function initOkoooMessageHandler() {
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    switch (message.type) {
      case 'OKOOO_START_CRAWLER':
        okoooMainCrawler.start()
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ success: false, message: String(error) }));
        return true;

      case 'OKOOO_STOP_CRAWLER':
        okoooMainCrawler.stop()
          .then(() => sendResponse({ success: true }))
          .catch(error => sendResponse({ success: false, message: String(error) }));
        return true;

      case 'OKOOO_START_REPAIR':
        okoooMainCrawler.startWithIds(message.ids)
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ success: false, message: String(error) }));
        return true;

      case 'OKOOO_START_REPAIR_TASKS':
        okoooMainCrawler.startWithTasks(message.tasks)
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ success: false, message: String(error) }));
        return true;

      case 'OKOOO_GET_STATUS':
        sendResponse({
          success: true,
          data: okoooMainCrawler.getStatus()
        });
        break;

      case 'OKOOO_OPEN_LIST':
        okoooListCrawler.openAndCapture(message.url)
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ success: false, message: String(error) }));
        return true;

      case 'OKOOO_LIST_STATUS':
        sendResponse({
          success: true,
          data: okoooListCrawler.getStatus()
        });
        break;

      // 让球盘爬虫消息处理
      case 'OKOOO_HANDICAP_START':
        okoooHandicapCrawler.start()
          .then(result => sendResponse(result))
          .catch(error => sendResponse({ success: false, message: String(error) }));
        return true;

      case 'OKOOO_HANDICAP_STOP':
        okoooHandicapCrawler.stop();
        sendResponse({ success: true });
        break;

      case 'OKOOO_HANDICAP_STATUS':
        sendResponse({
          success: true,
          data: okoooHandicapCrawler.getStats()
        });
        break;
    }
  });
}
