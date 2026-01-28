
// Native message types
export enum NativeMessageType {
  PROCESS_DATA = 'processData',
  CALL_TOOL = 'callTool',
  SERVER_STARTED = 'serverStarted',
  SERVER_STOPPED = 'serverStopped',
  ERROR_FROM_NATIVE_HOST = 'errorFromNativeHost',
  CONNECT_NATIVE = 'connectNative',
  START = 'start',
  PING_NATIVE = 'pingNative',
  DISCONNECT_NATIVE = 'disconnectNative',
}

// Tool names
export const TOOL_NAMES = {
  BROWSER: {
    NAVIGATE: 'navigate',
    CLOSE_TABS: 'close_tabs',
    GO_BACK_OR_FORWARD: 'go_back_or_forward',
    NETWORK_REQUEST: 'network_request',
    NETWORK_CAPTURE_START: 'network_capture_start',
    NETWORK_CAPTURE_STOP: 'network_capture_stop',
    BOOKMARK_SEARCH: 'bookmark_search',
    BOOKMARK_ADD: 'bookmark_add',
    BOOKMARK_DELETE: 'bookmark_delete',
    NETWORK_DEBUGGER_START: 'network_debugger_start',
    NETWORK_DEBUGGER_STOP: 'network_debugger_stop',
    GET_WINDOWS_AND_TABS: 'get_windows_and_tabs',
    CLICK: 'click',
    FILL: 'fill',
    INJECT_SCRIPT: 'inject_script',
    SEND_COMMAND_TO_INJECT_SCRIPT: 'send_command_to_inject_script',
    CONSOLE: 'console',
    SEARCH_TABS_CONTENT: 'search_tabs_content',
    SCREENSHOT: 'screenshot',
    WEB_FETCHER: 'web_fetcher',
    GET_INTERACTIVE_ELEMENTS: 'get_interactive_elements',
    KEYBOARD: 'keyboard',
    HISTORY: 'history',
  },
} as const;
