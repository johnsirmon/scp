export interface PiiPattern {
  name: string;
  pattern: RegExp;
  replacement: string;
}

export const PII_PATTERNS: PiiPattern[] = [
  { name: 'SUBSCRIPTION_ID', pattern: /\/subscriptions\/[a-f0-9-]{36}/gi, replacement: '[SUB_ID_#]' },
  { name: 'RESOURCE_GROUP', pattern: /\/resourceGroups\/[\w-]+/gi, replacement: '[RG_#]' },
  { name: 'PROVIDER', pattern: /\/providers\/Microsoft\.[\w/]+/gi, replacement: '[RESOURCE_#]' },
  { name: 'GUID', pattern: /\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b/gi, replacement: '[GUID_#]' },
  { name: 'MS_EMAIL', pattern: /\b[\w-]+@microsoft\.com\b/gi, replacement: '[MS_EMAIL_#]' },
  { name: 'EMAIL', pattern: /\b[\w.-]+@[\w-]+\.[\w.-]+\b/g, replacement: '[EMAIL_#]' },
  { name: 'IP_ADDRESS', pattern: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g, replacement: '[IP_#]' },
  { name: 'VM_NAME', pattern: /\bvm-[\w-]+/gi, replacement: '[VM_#]' },
  { name: 'PHONE', pattern: /\b\d{3}-\d{3}-\d{4}\b/g, replacement: '[PHONE_#]' },
  { name: 'UNC_PATH', pattern: /\\\\[\w-]+\\[\w\s]+/gi, replacement: '[UNC_PATH_#]' },
  { name: 'WIN_PATH', pattern: /[A-Z]:\\[\w\\\s.-]+/gi, replacement: '[WIN_PATH_#]' },
  { name: 'REGISTRY', pattern: /HKEY_[A-Z_]+\\[\w\\.-]+/gi, replacement: '[REGISTRY_#]' },
  { name: 'USER_PATH', pattern: /[a-zA-Z]:\\Users\\[^\\\s]+/gi, replacement: '[USER_PATH_#]' },
  { name: 'DB_SERVER', pattern: /server=[\w.-]+/gi, replacement: '[DB_SERVER_#]' },
  { name: 'DB_NAME', pattern: /database=\w+/gi, replacement: '[DB_NAME_#]' },
];
