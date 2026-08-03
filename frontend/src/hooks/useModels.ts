import { useState, useCallback } from 'react';
import { apiClient } from '../api/client';
import type { ModelEntry, ModelInput } from '../types/config';

/**
 * 模型注册表状态 hook：列表 + active + 增删改切换。
 * 每次变更后自动刷新列表；刷新失败只记日志，不抛错（避免误报"操作失败"）。
 */
export function useModels() {
  const [models, setModels] = useState<ModelEntry[]>([]);
  const [active, setActive] = useState('');
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.listModels();
      setModels(data.models);
      setActive(data.active_model);
    } catch (err) {
      console.error('Failed to load models:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const addModel = useCallback(async (input: ModelInput) => {
    const res = await apiClient.addModel(input);
    await refresh();
    return res;
  }, [refresh]);

  const updateModel = useCallback(async (name: string, patch: Partial<Omit<ModelEntry, 'name'>>) => {
    const res = await apiClient.updateModel(name, patch);
    await refresh();
    return res;
  }, [refresh]);

  const deleteModel = useCallback(async (name: string) => {
    const res = await apiClient.deleteModel(name);
    await refresh();
    return res;
  }, [refresh]);

  const setActiveModel = useCallback(async (name: string) => {
    const res = await apiClient.setActiveModel(name);
    await refresh();
    return res;
  }, [refresh]);

  return { models, active, loading, refresh, addModel, updateModel, deleteModel, setActiveModel };
}
