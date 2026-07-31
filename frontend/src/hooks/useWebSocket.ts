import { useRef, useState, useCallback, useEffect } from 'react';
import type { ServerMessage, ClientMessage, DisplayMessage, AskUserMessage } from '../types/chat';

interface UseWebSocketOptions {
  sessionId: string;
  onMessage: (msg: DisplayMessage) => void;
  onStreamingChange: (streaming: boolean) => void;
}

interface UseWebSocketReturn {
  send: (content: string) => void;
  cancel: () => void;
  answerUser: (requestId: string, answer: 'approved' | 'rejected', detail?: string) => void;
  connected: boolean;
  askUser: AskUserMessage | null;
  dismissAskUser: () => void;
}

export function useWebSocket({ sessionId, onMessage, onStreamingChange }: UseWebSocketOptions): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttempt = useRef(0);
  const mountedRef = useRef(true);
  const intentionalCloseRef = useRef(false);
  const [connected, setConnected] = useState(false);
  const [askUser, setAskUser] = useState<AskUserMessage | null>(null);

  // 当前正在累积的 Agent 消息
  const pendingMsgRef = useRef<DisplayMessage | null>(null);

  const connect = useCallback(() => {
    // 避免重复连接
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return;
    if (!mountedRef.current) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/chat/${sessionId || '_ephemeral'}`;

    try {
      intentionalCloseRef.current = false;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setConnected(true);
        reconnectAttempt.current = 0;
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const msg: ServerMessage = JSON.parse(event.data);
          handleServerMessage(msg);
        } catch {
          // 纯文本 chunk
          if (event.data) {
            appendToPending(event.data, false);
          }
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setConnected(false);
        // 如果是主动关闭（session 切换），不自动重连
        if (intentionalCloseRef.current) return;
        // 自动重连（指数退避）
        if (reconnectAttempt.current < 10) {
          const delay = Math.min(1000 * 2 ** reconnectAttempt.current, 30000);
          reconnectAttempt.current++;
          reconnectTimeout.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        // 错误时让浏览器自然处理，onclose 会随之触发并启动重连
        console.warn('[WS] Connection error');
      };
    } catch {
      // 连接失败，稍后重试
      if (!mountedRef.current) return;
      reconnectTimeout.current = setTimeout(connect, 3000);
    }
  }, [sessionId, onMessage, onStreamingChange]);

  const handleServerMessage = useCallback((msg: ServerMessage) => {
    switch (msg.type) {
      case 'chunk':
        appendToPending(msg.content, true);
        break;

      case 'tool_call':
        appendToolCall(msg.call_id, msg.tool, msg.args);
        break;

      case 'tool_result':
        completeToolCall(msg.call_id, msg.result, false);
        break;

      case 'tool_error':
        completeToolCall(msg.call_id, msg.error, true);
        break;

      case 'ask_user':
        setAskUser(msg);
        break;

      case 'done':
        flushPending();
        onStreamingChange(false);
        break;

      case 'interrupted':
        if (pendingMsgRef.current) {
          pendingMsgRef.current.interrupted = true;
          flushPending();
        }
        onStreamingChange(false);
        break;

      case 'error':
        flushPending();
        onStreamingChange(false);
        break;

      case 'pong':
        break;

      case 'session_info':
        // 服务端发送的会话元数据，仅记录
        break;
    }
  }, [onMessage, onStreamingChange]);

  function appendToPending(content: string, streaming: boolean) {
    if (!pendingMsgRef.current) {
      pendingMsgRef.current = {
        id: `agent-${Date.now()}`,
        role: 'agent',
        content: '',
        timestamp: Date.now(),
        isStreaming: streaming,
      };
      onStreamingChange(true);
    }
    pendingMsgRef.current.content += content;
    pendingMsgRef.current.isStreaming = streaming;
    // 通知更新（React 会合并渲染）
    onMessage({ ...pendingMsgRef.current });
  }

  function appendToolCall(callId: string, tool: string, args: Record<string, unknown>) {
    flushPending();
    const toolMsg: DisplayMessage = {
      id: `tool-${callId}`,
      role: 'tool',
      content: '',
      timestamp: Date.now(),
      toolCall: { call_id: callId, tool, args, status: 'running' },
    };
    onMessage(toolMsg);
  }

  function completeToolCall(callId: string, result: string, isError: boolean) {
    const toolMsg: DisplayMessage = {
      id: `tool-${callId}-done`,
      role: 'tool',
      content: result,
      timestamp: Date.now(),
      toolCall: {
        call_id: callId,
        tool: '',
        args: {},
        result,
        error: isError ? result : undefined,
        status: isError ? 'error' : 'success',
      },
    };
    onMessage(toolMsg);
  }

  function flushPending() {
    if (pendingMsgRef.current) {
      pendingMsgRef.current.isStreaming = false;
      onMessage({ ...pendingMsgRef.current });
      pendingMsgRef.current = null;
    }
  }

  const send = useCallback((content: string) => {
    flushPending();
    const userMsg: DisplayMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    onMessage(userMsg);

    const msg: ClientMessage = { type: 'chat', content };
    wsRef.current?.send(JSON.stringify(msg));
  }, [onMessage]);

  const cancel = useCallback(() => {
    const msg: ClientMessage = { type: 'cancel' };
    wsRef.current?.send(JSON.stringify(msg));
  }, []);

  const answerUser = useCallback((requestId: string, answer: 'approved' | 'rejected', detail?: string) => {
    const msg: ClientMessage = { type: 'user_answer', request_id: requestId, answer, detail };
    wsRef.current?.send(JSON.stringify(msg));
    setAskUser(null);
  }, []);

  const dismissAskUser = useCallback(() => setAskUser(null), []);

  useEffect(() => {
    mountedRef.current = true;
    intentionalCloseRef.current = false;
    connect();
    return () => {
      mountedRef.current = false;
      intentionalCloseRef.current = true;
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // 阻止 onclose 触发重连
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { send, cancel, answerUser, connected, askUser, dismissAskUser };
}
