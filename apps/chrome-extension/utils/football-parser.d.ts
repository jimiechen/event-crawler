export function initializeMCPSession(): Promise<string | null>;
export function getChromeWebContent(url: string, sessionId?: string): Promise<any>;
export function parseFootballMatches(html: string, rule: any): any[];
export function generateFootballReport(matches: any[]): string;
