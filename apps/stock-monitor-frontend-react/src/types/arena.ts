export interface PromptTemplate {
  id: number;
  key: string;
  name: string;
  description?: string;
  template_text: string;
  system_template_text?: string;
  is_system: boolean;
  is_deleted: string; // 'true' | 'false' - kept as string to match backend literal "false"/"true" if that's what it returns, though boolean is better if backend serializes it as bool. Checking schema: is_deleted: str = "false". So string is correct.
  created_by: string;
  created_at: string;
  updated_at?: string;
}

export interface PromptBinding {
  id: number;
  account_id: number;
  prompt_template_id: number;
  account_name?: string;
  account_model?: string;
  prompt_name?: string;
  updated_by?: string;
}

export interface TradingAccount {
  id: number;
  name: string;
  account_type: string;
  model?: string;
  status: string;
}

export interface SignalDefinition {
  id: number;
  signal_name: string;
  description?: string;
  trigger_condition: any; // JSON
  enabled: boolean;
  created_at: string;
}

export interface SignalPool {
  id: number;
  pool_name: string;
  signal_ids: number[];
  symbols: string[];
  logic: string; // 'AND' | 'OR'
  enabled: boolean;
  created_at: string;
}

export interface AIDecisionResult {
  id: number;
  stock_code: string;
  trade_date: string;
  decision_json: any;
  model_name: string;
  template_name?: string;
  primary_operation?: string;
  primary_reason?: string;
  created_at: string;
  // trigger_context?: any; // Removed as it's not in AIDecisionResponse
}

export interface ScheduledTask {
  id: number;
  name: string;
  task_type: string;
  cron_expression: string;
  is_active: boolean;
  description?: string;
  last_run_at?: string;
  last_run_status?: string; // 'success' | 'failed' | 'running' etc. Backend is str.
  next_run_at?: string;
}
