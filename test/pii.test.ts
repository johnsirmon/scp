import { describe, it, expect } from 'vitest';
import { redactPii, rehydrate } from '../src/pii/redactor.js';

describe('PII Redactor', () => {
  it('redacts email addresses', () => {
    const { redacted } = redactPii('Contact user@example.com for details');
    expect(redacted).not.toContain('user@example.com');
    expect(redacted).toMatch(/\[EMAIL_\d+\]/);
  });

  it('redacts IP addresses', () => {
    const { redacted } = redactPii('Server at 192.168.1.100 failed');
    expect(redacted).not.toContain('192.168.1.100');
    expect(redacted).toMatch(/\[IP_\d+\]/);
  });

  it('redacts GUIDs', () => {
    const guid = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
    const { redacted } = redactPii(`Subscription ID: ${guid}`);
    expect(redacted).not.toContain(guid);
    expect(redacted).toMatch(/\[GUID_\d+\]/);
  });

  it('stores mappings for rehydration', () => {
    const email = 'admin@example.com';
    const { redacted, mappings } = redactPii(`Email: ${email}`);
    expect(Object.values(mappings)).toContain(email);
    const restored = rehydrate(redacted, mappings);
    expect(restored).toContain(email);
  });

  it('handles text with no PII', () => {
    const text = 'Normal support case with no sensitive data';
    const { redacted, mappings } = redactPii(text);
    expect(redacted).toBe(text);
    expect(Object.keys(mappings)).toHaveLength(0);
  });
});
