import { http, HttpResponse } from 'msw';
import { mockPrompts } from './data/prompts';
import { mockSignals, mockSignalPools } from './data/signals';
import { mockAccounts } from './data/accounts';
import { mockTasks } from './data/tasks';

// Ensure this matches api.ts BASE_URL. 
// Note: api.ts uses import.meta.env.VITE_API_BASE_URL || '/api/v1'.
// During test, axios might use localhost if not configured, or if we use relative paths in axios, 
// jsdom environment might default to http://localhost:3000.
// However, api.ts sets baseURL to '/api/v1'.
// In axios with jsdom, a relative URL '/api/v1' is resolved against window.location.origin (usually http://localhost:3000).
// But we want to be safe. MSW can intercept relative paths if we just use '/api/v1/...' or absolute 'http://localhost:3000/api/v1/...'.
// Or if we configured axios to use a specific host.
// Let's assume axios uses the relative path. MSW intercepting '/api/v1/...' works for requests to origin + '/api/v1/...'.
const API_PREFIX = '/api/v1';

export const handlers = [
  // Prompts
  http.get(`${API_PREFIX}/arena/prompts`, () => {
    return HttpResponse.json(mockPrompts);
  }),
  http.post(`${API_PREFIX}/arena/prompts`, async ({ request }) => {
    const newPrompt = await request.json() as any;
    return HttpResponse.json({ ...newPrompt, id: Date.now() });
  }),

  // Signals
  http.get(`${API_PREFIX}/arena/signals`, () => {
    return HttpResponse.json(mockSignals);
  }),
  http.get(`${API_PREFIX}/arena/signal-pools`, () => {
    return HttpResponse.json(mockSignalPools);
  }),

  // Accounts
  http.get(`${API_PREFIX}/arena/accounts`, () => {
    return HttpResponse.json(mockAccounts);
  }),

  // Tasks
  http.get(`${API_PREFIX}/timed-task/scheduled/list`, () => {
    return HttpResponse.json({ success: true, data: mockTasks });
  }),
];
