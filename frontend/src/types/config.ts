export interface ConfigSchemaField {
  type: 'string' | 'number' | 'boolean' | 'select';
  label: string;
  default: string | number | boolean;
  options?: string[];
  description?: string;
  minimum?: number;
  maximum?: number;
}

export interface ConfigSchema {
  title: string;
  fields: Record<string, ConfigSchemaField>;
}

export type ConfigSchemas = Record<string, ConfigSchema>;

export interface ConfigValues {
  [key: string]: unknown;
}

/** 模型注册表中的一个模型项（api_key 由后端掩码返回） */
export interface ModelEntry {
  name: string;
  label: string;
  base_url: string;
  api_key: string;
  model: string;
}

/** 添加模型的请求体 */
export interface ModelInput {
  name: string;
  label: string;
  base_url: string;
  api_key: string;
  model: string;
}

export interface ModelListResponse {
  active_model: string;
  models: ModelEntry[];
}
