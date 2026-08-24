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
  status: string;
  source_email_id: string | null;
  source_email_received_at: string | null;
  person: Person | null;
  summary: Summary | null;
  created_at: string;
  updated_at: string;
}
