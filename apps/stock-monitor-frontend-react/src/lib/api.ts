import axios from 'axios';
import type { PromptTemplate, SignalDefinition, SignalPool, AIDecisionResult, PromptBinding, TradingAccount, ScheduledTask } from '@/types/arena';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const arenaApi = {
  // Prompts
  getPrompts: () => api.get<{templates: PromptTemplate[], bindings: PromptBinding[]}>('/arena/prompts'),
  createPrompt: (data: Partial<PromptTemplate>) => api.post<PromptTemplate>('/arena/prompts', data),
  updatePrompt: (id: number, data: Partial<PromptTemplate>) => api.put<PromptTemplate>(`/arena/prompts/${id}`, data),
  deletePrompt: (id: number) => api.delete(`/arena/prompts/${id}`),
  copyPrompt: (id: number, data: { newName?: string, createdBy: string }) => api.post<PromptTemplate>(`/arena/prompts/${id}/copy`, data),

  // Bindings
  upsertBinding: (data: Partial<PromptBinding>) => api.post<PromptBinding>('/arena/prompts/bindings', data),
  deleteBinding: (id: number) => api.delete(`/arena/prompts/bindings/${id}`),

  // Accounts
  getAccounts: () => api.get<TradingAccount[]>('/arena/accounts'),

  // Signals
  getSignals: () => api.get<{signals: SignalDefinition[], pools: SignalPool[]}>('/arena/signals'),
  createSignal: (data: Partial<SignalDefinition>) => api.post<SignalDefinition>('/arena/signals/definitions', data),
  updateSignal: (id: number, data: Partial<SignalDefinition>) => api.put<SignalDefinition>(`/arena/signals/definitions/${id}`, data),
  deleteSignal: (id: number) => api.delete(`/arena/signals/definitions/${id}`),
  
  // Signal Pools
  getSignalPools: () => api.get<SignalPool[]>('/arena/signal-pools'),
  createSignalPool: (data: Partial<SignalPool>) => api.post<SignalPool>('/arena/signal-pools', data),
  updateSignalPool: (id: number, data: Partial<SignalPool>) => api.put<SignalPool>(`/arena/signal-pools/${id}`, data),
  deleteSignalPool: (id: number) => api.delete(`/arena/signal-pools/${id}`),

  // AI Decisions
  getDecisions: (stockCode?: string) => api.get<AIDecisionResult[]>('/arena/decisions', { params: { stock_code: stockCode } }),
};

export const schedulerApi = {
    getTasks: () => api.get<{success: boolean, data: ScheduledTask[]}>('/v1/timed-task/scheduled/list'),
};

// Adapters for PromptManager
export const getPromptTemplates = async () => {
    const res = await arenaApi.getPrompts();
    return res.data;
};
export const updatePromptTemplate = async (key: string, data: any) => {
    // Note: API uses ID, but UI might pass key. Assuming we can find ID or API supports key.
    // For now, if key is passed but we need ID, this might fail. 
    // But PromptManager passes selectedTemplate.key. 
    // Let's assume we change PromptManager to pass ID or we handle it.
    // Actually PromptManager calls updatePromptTemplate(selectedTemplate.key, ...)
    // We should probably change PromptManager to use ID.
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
    const res = await arenaApi.getSignals();
    return res.data;
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
