import { describe, it, expect } from 'vitest';
import { getPolicy, STRICT_POLICY, TRUSTED_POLICY } from '../src/policy/profiles.js';

describe('Policy Profiles', () => {
  it('strict policy has all controls enabled', () => {
    expect(STRICT_POLICY.requireRedaction).toBe(true);
    expect(STRICT_POLICY.allowFullRehydration).toBe(false);
    expect(STRICT_POLICY.encryptVault).toBe(true);
    expect(STRICT_POLICY.auditLog).toBe(true);
    expect(STRICT_POLICY.outboundScrub).toBe(true);
  });

  it('trusted policy allows rehydration', () => {
    expect(TRUSTED_POLICY.allowFullRehydration).toBe(true);
    expect(TRUSTED_POLICY.requireRedaction).toBe(true);
    expect(TRUSTED_POLICY.encryptVault).toBe(true);
  });

  it('getPolicy returns strict for "strict"', () => {
    expect(getPolicy('strict')).toEqual(STRICT_POLICY);
  });

  it('getPolicy returns trusted as default', () => {
    expect(getPolicy('trusted')).toEqual(TRUSTED_POLICY);
    expect(getPolicy('unknown')).toEqual(TRUSTED_POLICY);
  });
});
