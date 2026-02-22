import { PII_PATTERNS } from './patterns.js';

export interface RedactionResult {
  redacted: string;
  mappings: Record<string, string>;
}

export function redactPii(text: string): RedactionResult {
  let redacted = text;
  const mappings: Record<string, string> = {};
  const counters: Record<string, number> = {};

  for (const { replacement, pattern } of PII_PATTERNS) {
    redacted = redacted.replace(pattern, (match) => {
      const base = replacement.replace('#', '');
      counters[base] = (counters[base] ?? 0) + 1;
      const token = replacement.replace('#', String(counters[base]));
      mappings[token] = match;
      return token;
    });
  }

  return { redacted, mappings };
}

export function rehydrate(redacted: string, mappings: Record<string, string>): string {
  let result = redacted;
  for (const [token, original] of Object.entries(mappings)) {
    // Escape special regex chars in token
    const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    result = result.replace(new RegExp(escaped, 'g'), original);
  }
  return result;
}
