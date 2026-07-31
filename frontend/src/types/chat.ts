// WebSocket 消息类型定义

export interface WsMessageBase {
  type: string;
}

// ── Client → Server ──
export interface ChatMessage extends WsMessageBase {
  type: 'chat';
  content: string;
}

export interface CancelMessage extends WsMessageBase {
  type: 'cancel';
}

export interface UserAnswerMessage extends WsMessageBase {
  type: 'user_answer';
  request_id: string;
  answer: 'approved' | 'rejected';
  detail?: string;
}

export type ClientMessage = ChatMessage | CancelMessage | UserAnswerMessage | { type: 'ping' };

// ── Server → Client ──
export interface ChunkMessage extends WsMessageBase {
  type: 'chunk';
  content: string;
}

export interface ToolCallMessage extends WsMessageBase {
  type: 'tool_call';
  call_id: string;
  tool: string;
  args: Record<string, unknown>;
}

export interface ToolResultMessage extends WsMessageBase {
  type: 'tool_result';
  call_id: string;
  tool: string;
  result: string;
}

export interface ToolErrorMessage extends WsMessageBase {
  type: 'tool_error';
  call_id: string;
  tool: string;
  error: string;
}

export interface AskUserMessage extends WsMessageBase {
  type: 'ask_user';
  request_id: string;
  question: string;
}

export interface DoneMessage extends WsMessageBase {
  type: 'done';
}

export interface InterruptedMessage extends WsMessageBase {
  type: 'interrupted';
}

export interface ErrorMessage extends WsMessageBase {
  type: 'error';
  message: string;
}

export interface SessionInfoMessage extends WsMessageBase {
  type: 'session_info';
  session_id: string;
  message_count: number;
}

export type ServerMessage =
  | ChunkMessage
  | ToolCallMessage
  | ToolResultMessage
  | ToolErrorMessage
  | AskUserMessage
  | DoneMessage
  | InterruptedMessage
  | ErrorMessage
  | SessionInfoMessage
  | { type: 'pong' };

// ── 消息显示模型（UI 层使用）──
export type DisplayMessageRole = 'user' | 'agent' | 'tool' | 'system';

export interface DisplayMessage {
  id: string;
  role: DisplayMessageRole;
  content: string;
  timestamp: number;
  toolCall?: {
    call_id: string;
    tool: string;
    args: Record<string, unknown>;
    result?: string;
    error?: string;
    status: 'running' | 'success' | 'error';
  };
  interrupted?: boolean;
  isStreaming?: boolean;
}
