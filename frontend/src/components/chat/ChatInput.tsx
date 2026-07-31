import React, { useState, useRef, useCallback, KeyboardEvent } from 'react';
import { Send, Square } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;
  onCancel: () => void;
  streaming: boolean;
  disabled: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, onCancel, streaming, disabled }) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div
        className={`flex items-end gap-2 bg-white rounded-2xl border px-4 py-3 shadow-sm transition-all duration-300
          ${streaming ? 'border-[#0066CC] animate-breathe-border' : 'border-[#E5E5EA] hover:border-[#D2D2D7]'}
          ${disabled ? 'opacity-50' : ''}`}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? '连接断开中...' : '输入消息... (Enter 发送, Shift+Enter 换行)'}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent text-[15px] leading-relaxed placeholder-[#AEAEB2]
            focus:outline-none max-h-[160px]"
        />
        {streaming ? (
          <button
            onClick={onCancel}
            className="flex-shrink-0 p-2 rounded-full bg-[#FF3B30] text-white
              hover:bg-red-600 transition-colors active:scale-95"
            title="停止生成"
          >
            <Square size={16} fill="currentColor" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            className="flex-shrink-0 p-2 rounded-full transition-all duration-200
              enabled:bg-[#0066CC] enabled:text-white enabled:hover:bg-[#0077ED]
              enabled:active:scale-95
              disabled:bg-[#ECEDF0] disabled:text-[#AEAEB2]"
            title="发送"
          >
            <Send size={16} />
          </button>
        )}
      </div>
    </div>
  );
};
