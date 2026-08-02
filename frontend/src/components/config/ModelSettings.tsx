import React, { useState, useEffect } from 'react';
import { useConfig } from '../../hooks/useConfig';
import { Button } from '../shared/Button';

export const ModelSettings: React.FC = () => {
  const { currentConfig, loadConfig, updateConfig } = useConfig();
  const [model, setModel] = useState('deepseek-v4-pro');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadConfig('agent');
  }, [loadConfig]);

  useEffect(() => {
    if (currentConfig.agent?.chat_model_name) {
      setModel(currentConfig.agent.chat_model_name as string);
    }
  }, [currentConfig.agent]);

  const handleSave = async () => {
    setSaving(true);
    await updateConfig('agent', { chat_model_name: model });
    setSaving(false);
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-[#6E6E73] mb-1.5 font-sidebar">
          聊天模型
        </label>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="w-full px-3 py-2 text-sm rounded-lg border border-[#E5E5EA] bg-white
            focus:outline-none focus:border-[#0066CC] focus:ring-1 focus:ring-[#0066CC]/20
            font-body"
        >
          <option value="deepseek-v4-pro">DeepSeek V4 Pro</option>
          <option value="deepseek-v4-flash">DeepSeek V4 Flash (更快)</option>
        </select>
        <p className="text-[11px] text-[#AEAEB2] mt-1 font-sidebar">
          Agent 主对话使用的 DeepSeek 模型。Pro 更智能，Flash 更快。
        </p>
      </div>
      <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
        {saving ? '保存中...' : '保存模型设置'}
      </Button>
    </div>
  );
};
