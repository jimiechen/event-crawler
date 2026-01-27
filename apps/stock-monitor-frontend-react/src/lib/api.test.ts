import { describe, it, expect } from 'vitest';
import { arenaApi, fetchSignals, schedulerApi } from './api';
import { mockPrompts } from '@/mocks/data/prompts';
import { mockSignals, mockSignalPools } from '@/mocks/data/signals';
import { mockAccounts } from '@/mocks/data/accounts';
import { mockTasks } from '@/mocks/data/tasks';

describe('API Integration Tests with MSW', () => {
  it('fetches prompts successfully', async () => {
    const response = await arenaApi.getPrompts();
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockPrompts);
  });

  it('fetches signals and pools successfully (aggregated)', async () => {
    const result = await fetchSignals();
    expect(result.signals).toEqual(mockSignals);
    expect(result.pools).toEqual(mockSignalPools);
  });

  it('fetches accounts successfully', async () => {
    const response = await arenaApi.getAccounts();
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockAccounts);
  });

  it('fetches scheduled tasks successfully', async () => {
    const response = await schedulerApi.getTasks();
    expect(response.status).toBe(200);
    expect(response.data.success).toBe(true);
    expect(response.data.data).toEqual(mockTasks);
  });
});
