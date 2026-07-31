import React from 'react';
import type { DisplayMessage } from '../../types/chat';

export const UserBubble: React.FC<{ message: DisplayMessage }> = ({ message }) => (
  <div className="flex justify-end">
    <div className="max-w-[80%] bg-[#007AFF] text-white rounded-2xl rounded-br-md px-4 py-2.5 shadow-sm">
      <p className="text-[15px] leading-relaxed whitespace-pre-wrap break-words">
        {message.content}
      </p>
    </div>
  </div>
);
