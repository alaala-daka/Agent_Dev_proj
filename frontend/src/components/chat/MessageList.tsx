import React, { useRef, useEffect } from 'react';
import type { DisplayMessage } from '../../types/chat';
import { AgentBubble } from './AgentBubble';
import { UserBubble } from './UserBubble';
import { ToolCallBubble } from './ToolCallBubble';

interface MessageListProps {
  messages: DisplayMessage[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 去重：相同 ID 的消息只保留最后一个（流式更新）
  const deduped = messages.reduce<DisplayMessage[]>((acc, msg) => {
    const existing = acc.findIndex(m => m.id === msg.id);
    if (existing >= 0) {
      acc[existing] = msg;
    } else {
      acc.push(msg);
    }
    return acc;
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      {deduped.map((msg) => {
        switch (msg.role) {
          case 'user':
            return <UserBubble key={msg.id} message={msg} />;
          case 'agent':
            return <AgentBubble key={msg.id} message={msg} />;
          case 'tool':
            return <ToolCallBubble key={msg.id} message={msg} />;
          default:
            return null;
        }
      })}
      <div ref={bottomRef} />
    </div>
  );
};
