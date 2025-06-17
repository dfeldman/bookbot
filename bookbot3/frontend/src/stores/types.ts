export interface Job {
  job_id: string;
  book_id: string;
  job_type: string;
  state: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  props: Record<string, any>;
  result: Record<string, any> | null;
  error_message: string | null;
  created_at: string; // ISO date string
  started_at: string | null; // ISO date string
  ended_at: string | null; // ISO date string
  updated_at: string | null; // ISO date string
  progress?: number;
  status_message?: string;
  total_cost?: number; // Added to store aggregated LLM cost for the job
  // Add any other relevant fields from your backend Job model
}

// You can add other shared types here, for example:
// export interface Book { ... }
// export interface Chunk { ... }
