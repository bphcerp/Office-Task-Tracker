export type TaskStatusValue = 'todo' | 'in_progress' | 'done';

export interface Person {
  id: number;
  name: string;
  email: string | null;
}

export interface Summary {
  id: number;
  body: string;
}

export interface Task {
  id: number;
  title: string;
  status: TaskStatusValue;
  source_email_id: string | null;
  source_email_received_at: string | null;
  person: Person | null;
  summary: Summary | null;
  created_at: string;
  updated_at: string;
}

export interface IngestResult {
  scraped: number;
  classified: number;
  created_tasks: number;
}
