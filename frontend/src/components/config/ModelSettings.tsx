import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Pencil, X, CheckCircle2 } from 'lucide-react';
import { useModels } from '../../hooks/useModels';
import { Button } from '../shared/Button';
import { Toast } from '../shared/Toast';
import type { ModelEntry } from '../../types/config';

interface ToastState {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

interface FormState {
  name: string;
  label: string;
  base_url: string;
  api_key: string;
  model: string;
}

const emptyForm: FormState = { name: '', label: '', base_url: '', api_key: '', model: '' };

const Field: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
}> = ({ label, value, onChange, placeholder, type = 'text', disabled = false }) => (
  <div>
    <label className="block text-[11px] font-medium text-[#6E6E73] mb-1 font-sidebar">{label}</label>
    <input
      type={type}
      value={value}
      disabled={disabled}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-1.5 text-sm rounded-lg border border-[#E5E5EA] bg-white
        focus:outline-none focus:border-[#0066CC] focus:ring-1 focus:ring-[#0066CC]/20 font-body
        disabled:bg-[#F0F0F2] disabled:text-[#AEAEB2]"
    />
  </div>
);

export const ModelSettings: React.FC = () => {
  const { models, active, loading, refresh, addModel, updateModel, deleteModel, setActiveModel } = useModels();
  const [showForm, setShowForm] = useState(false);
  const [editingName, setEditingName] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const showToast = (message: string, type: ToastState['type'] = 'success') => {
    setToast({ message, type });
  };

  const openAdd = () => {
    setEditingName(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const openEdit = (m: ModelEntry) => {
    setEditingName(m.name);
    // api_key 不回填（后端只返回掩码，回填会覆盖真实 key）；留空 = 保留原 key
    setForm({ name: m.name, label: m.label, base_url: m.base_url, api_key: '', model: m.model });
    setShowForm(true);
  };

  const handleSubmit = async () => {
    if (!form.model.trim()) {
      showToast('请填写模型名 (model)', 'error');
      return;
    }
    if (!editingName && !form.name.trim()) {
      showToast('请填写模型标识 (name)', 'error');
      return;
    }
    setSaving(true);
    try {
      if (editingName) {
        await updateModel(editingName, {
          label: form.label,
          base_url: form.base_url,
          model: form.model.trim(),
          ...(form.api_key.trim() ? { api_key: form.api_key.trim() } : {}),
        });
        showToast('模型已更新');
      } else {
        await addModel({
          name: form.name.trim(),
          label: form.label,
          base_url: form.base_url.trim(),
          api_key: form.api_key.trim(),
          model: form.model.trim(),
        });
        showToast('模型已添加');
      }
      setShowForm(false);
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : '操作失败', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleSetActive = async (name: string) => {
    if (name === active) return;
    try {
      await setActiveModel(name);
      showToast('已切换，新会话立即使用该模型；已打开的对话请刷新后使用', 'success');
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : '切换失败', 'error');
    }
  };

  const handleDelete = async (m: ModelEntry) => {
    if (!window.confirm(`确定删除模型「${m.label || m.name}」？`)) return;
    try {
      await deleteModel(m.name);
      showToast('模型已删除');
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : '删除失败', 'error');
    }
  };

  return (
    <div className="space-y-4">
      {/* 模型列表 */}
      {loading && models.length === 0 ? (
        <p className="text-[11px] text-[#AEAEB2] font-sidebar">加载中...</p>
      ) : models.length === 0 ? (
        <p className="text-[11px] text-[#AEAEB2] font-sidebar">尚未配置模型。点击下方"添加模型"开始。</p>
      ) : (
        <div className="space-y-2">
          {models.map((m) => {
            const isActive = m.name === active;
            return (
              <div
                key={m.name}
                className={`rounded-lg border p-3 transition-colors ${
                  isActive ? 'border-[#0066CC]/40 bg-blue-50/40' : 'border-[#E5E5EA] bg-white'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-sm font-medium text-[#1D1D1F] font-sidebar truncate">
                      {m.label || m.name}
                    </span>
                    {isActive && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium text-[#30B158] font-sidebar shrink-0">
                        <CheckCircle2 size={12} /> 当前
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {!isActive && (
                      <Button variant="secondary" size="sm" onClick={() => handleSetActive(m.name)}>
                        设为当前
                      </Button>
                    )}
                    <button
                      onClick={() => openEdit(m)}
                      title="编辑"
                      className="p-1.5 rounded-md text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F0F0F2] transition-colors"
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(m)}
                      title="删除"
                      className="p-1.5 rounded-md text-[#6E6E73] hover:text-[#FF3B30] hover:bg-red-50 transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <div className="mt-1.5 space-y-0.5 text-[11px] text-[#6E6E73] font-body break-all">
                  <div>
                    <span className="text-[#AEAEB2] font-sidebar">model:</span> {m.model}
                  </div>
                  <div>
                    <span className="text-[#AEAEB2] font-sidebar">base_url:</span>{' '}
                    {m.base_url || 'DeepSeek（环境变量）'}
                  </div>
                  <div>
                    <span className="text-[#AEAEB2] font-sidebar">api_key:</span>{' '}
                    {m.api_key ? `已设置 (${m.api_key})` : '未设置（使用环境变量）'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 添加 / 编辑表单 */}
      {showForm && (
        <div className="rounded-lg border border-[#E5E5EA] bg-[#F9F9FB] p-3 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#1D1D1F] font-sidebar">
              {editingName ? '编辑模型' : '添加模型'}
            </span>
            <button
              onClick={() => setShowForm(false)}
              className="text-[#6E6E73] hover:text-[#1D1D1F] transition-colors"
            >
              <X size={14} />
            </button>
          </div>
          {!editingName && (
            <Field
              label="标识 (name，唯一，创建后不可改)"
              value={form.name}
              onChange={(v) => setForm((f) => ({ ...f, name: v }))}
              placeholder="如 my-provider"
            />
          )}
          <Field
            label="显示名 (label)"
            value={form.label}
            onChange={(v) => setForm((f) => ({ ...f, label: v }))}
            placeholder="如 My Model"
          />
          <Field
            label="API 地址 (base_url)"
            value={form.base_url}
            onChange={(v) => setForm((f) => ({ ...f, base_url: v }))}
            placeholder="https://api.example.com/v1（留空 = 内置 DeepSeek）"
          />
          <Field
            label="API Key"
            type="password"
            value={form.api_key}
            onChange={(v) => setForm((f) => ({ ...f, api_key: v }))}
            placeholder={editingName ? '留空则保留原 key' : '留空则使用环境变量'}
          />
          <Field
            label="模型名 (model)"
            value={form.model}
            onChange={(v) => setForm((f) => ({ ...f, model: v }))}
            placeholder="如 gpt-4o-mini / deepseek-chat"
          />
          <div className="flex gap-2">
            <Button variant="primary" size="sm" onClick={handleSubmit} disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setShowForm(false)}>
              取消
            </Button>
          </div>
        </div>
      )}

      {/* 添加按钮 */}
      {!showForm && (
        <Button variant="secondary" size="sm" onClick={openAdd} className="w-full">
          <Plus size={14} /> 添加模型
        </Button>
      )}

      <p className="text-[11px] text-[#AEAEB2] font-sidebar">
        当前 active 模型驱动主对话、会话标题、RAG 总结与文件切分。任意符合 OpenAI 协议的端点即可，无需 DeepSeek。
      </p>

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};
