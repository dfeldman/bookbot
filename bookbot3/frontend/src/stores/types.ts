export interface Job {
  job_id: string;
  book_id: string;
  chunk_id?: string | null;
  job_type: string;
  state: 'pending' | 'running' | 'completed' | 'failed' | 'error' | 'cancelled' | 'waiting';
  props?: Record<string, any>;
  result?: Record<string, any> | null;
  error_message?: string | null;
  created_at: string; // ISO date string
  started_at?: string | null; // ISO date string
  ended_at?: string | null; // ISO date string
  updated_at?: string | null; // ISO date string
  progress?: number;
  status_message?: string;
  total_cost?: number; // Added to store aggregated LLM cost for the job
}

export interface Chunk {
  chunk_id: string;
  book_id: string;
  type: 'prose' | 'bot' | 'bot_task' | 'scene';
  title: string;
  text: string;
  props?: Record<string, any>;
  is_locked?: boolean;
  locked_by_job_id?: string | null;
  is_deleted: boolean;
  is_latest: boolean;
  version: number;
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface Book {
  book_id: string;
  user_id: string;
  title: string;
  description: string;
  props: Record<string, any>;
  is_locked: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  word_count?: number;
  chunks?: Chunk[];
}

export interface LLMInfo {
  id: string;
  name: string;
  description: string;
  company: string;
  router: string;
  context_length: number;
  input_cost_per_mtok: number;
  output_cost_per_mtok: number;
  seconds_per_output_mtok: number;
  groups: string[];
  quality_score: number;
}

export interface ContextData {
  available: boolean;
  tags?: string[];
  outline_section?: string;
  characters_sections?: string[];
  settings_sections?: string[];
}
