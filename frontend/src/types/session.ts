export interface Session {
  session_id: string;
  message_count: number;
  created_at?: string;
  updated_at?: string;
  size_bytes?: number;
  size_human?: string;
}
