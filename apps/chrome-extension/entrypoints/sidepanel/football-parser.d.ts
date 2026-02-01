declare module '../../utils/football-parser.js' {
  export function initializeMCPSession(): Promise<void>;
  export function getChromeWebContent(tabId: number): Promise<string>;
  export function parseFootballMatches(html: string, rule: any): any[];
  export function generateFootballReport(matches: any[]): string;
}
