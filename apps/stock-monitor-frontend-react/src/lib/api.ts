import axios from 'axios';
import type { PromptTemplate, SignalDefinition, SignalPool, AIDecisionResult, PromptBinding, TradingAccount, ScheduledTask } from '@/types/arena';

// Updated to match backend prefix /api/v1
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const arenaApi = {
  // Prompts
  // Backend returns List[PromptTemplateResponse]
  getPrompts: () => api.get<PromptTemplate[]>('/arena/prompts'),
  createPrompt: (data: Partial<PromptTemplate>) => api.post<PromptTemplate>('/arena/prompts', data),
  updatePrompt: (id: number, data: Partial<PromptTemplate>) => api.put<PromptTemplate>(`/arena/prompts/${id}`, data),
  deletePrompt: (id: number) => api.delete(`/arena/prompts/${id}`),
  // Copy and Bindings are not yet implemented in backend, mocking or keeping for future
  copyPrompt: (id: number, data: { newName?: string, createdBy: string }) => api.post<PromptTemplate>(`/arena/prompts/${id}/copy`, data),

  // Bindings
  upsertBinding: (data: Partial<PromptBinding>) => api.post<PromptBinding>('/arena/prompts/bindings', data),
  deleteBinding: (id: number) => api.delete(`/arena/prompts/bindings/${id}`),

  // Accounts
  // Not implemented in backend yet, will be mocked
  getAccounts: () => api.get<TradingAccount[]>('/arena/accounts'),

  // Signals
  // Split into signals and pools as per backend implementation
  getSignals: () => api.get<SignalDefinition[]>('/arena/signals'),
  createSignal: (data: Partial<SignalDefinition>) => api.post<SignalDefinition>('/arena/signals', data), // Backend uses /signals, not /signals/definitions
  updateSignal: (id: number, data: Partial<SignalDefinition>) => api.put<SignalDefinition>(`/arena/signals/${id}`, data),
  deleteSignal: (id: number) => api.delete(`/arena/signals/${id}`),
  
  // Signal Pools
  getSignalPools: () => api.get<SignalPool[]>('/arena/signal-pools'),
  createSignalPool: (data: Partial<SignalPool>) => api.post<SignalPool>('/arena/signal-pools', data),
  updateSignalPool: (id: number, data: Partial<SignalPool>) => api.put<SignalPool>(`/arena/signal-pools/${id}`, data),
  deleteSignalPool: (id: number) => api.delete(`/arena/signal-pools/${id}`),

  // AI Decisions
  getDecisions: (stockCode?: string) => api.get<AIDecisionResult[]>('/arena/decisions', { params: { stock_code: stockCode } }),
};

export const schedulerApi = {
    // Backend: /api/v1/timed-task/scheduled/list -> returns BaseResponse { success: true, data: [] }
    getTasks: () => api.get<{success: boolean, data: ScheduledTask[]}>('/timed-task/scheduled/list'),
};

// Adapters for PromptManager
export const getPromptTemplates = async () => {
    // Frontend expects { templates: [], bindings: [] } but backend only returns templates.
    // We synthesize the structure here for frontend compatibility until bindings are implemented.
    const res = await arenaApi.getPrompts();
    return {
        templates: res.data,
        bindings: [] as PromptBinding[] // Mock empty bindings
    };
};

export const updatePromptTemplate = async (key: string, data: any) => {
    throw new Error("Use updatePromptTemplateById");
};
export const updatePromptTemplateById = async (id: number, data: any) => {
    const res = await arenaApi.updatePrompt(id, data);
    return res.data;
};
export const createPromptTemplate = async (data: any) => (await arenaApi.createPrompt(data)).data;
export const deletePromptTemplate = async (id: number) => (await arenaApi.deletePrompt(id)).data;
export const copyPromptTemplate = async (id: number, data: any) => (await arenaApi.copyPrompt(id, data)).data;
export const updatePromptTemplateName = async (id: number, data: any) => (await arenaApi.updatePrompt(id, data)).data;

export const upsertPromptBinding = async (data: any) => (await arenaApi.upsertBinding(data)).data;
export const deletePromptBinding = async (id: number) => (await arenaApi.deleteBinding(id)).data;
export const getAccounts = async () => (await arenaApi.getAccounts()).data;
export const getVariablesReference = async (lang: string) => ({ content: "Variables reference not implemented yet." });

// Adapters for SignalManager
export const fetchSignals = async () => {
    // Parallel fetch for signals and pools
    const [signalsRes, poolsRes] = await Promise.all([
        arenaApi.getSignals(),
        arenaApi.getSignalPools()
    ]);
    
    return {
        signals: signalsRes.data,
        pools: poolsRes.data
    };
};
export const createSignal = async (data: any) => (await arenaApi.createSignal(data)).data;
export const updateSignal = async (id: number, data: any) => (await arenaApi.updateSignal(id, data)).data;
export const deleteSignal = async (id: number) => (await arenaApi.deleteSignal(id)).data;
export const createPool = async (data: any) => (await arenaApi.createSignalPool(data)).data;
export const updatePool = async (id: number, data: any) => (await arenaApi.updateSignalPool(id, data)).data;
export const deletePool = async (id: number) => (await arenaApi.deleteSignalPool(id)).data;
export const fetchTriggerLogs = async () => []; // Not implemented
export const fetchMetricAnalysis = async () => null; // Not implemented

export type { PromptTemplate, PromptBinding, TradingAccount, SignalDefinition, SignalPool };
