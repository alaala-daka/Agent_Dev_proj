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
