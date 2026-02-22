import { PolicyConfig } from './types.js';

export const STRICT_POLICY: PolicyConfig = {
  profile: 'strict',
  requireRedaction: true,
  allowFullRehydration: false,
  encryptVault: true,
  auditLog: true,
  outboundScrub: true,
};

export const TRUSTED_POLICY: PolicyConfig = {
  profile: 'trusted',
  requireRedaction: true,
  allowFullRehydration: true,
  encryptVault: true,
  auditLog: false,
  outboundScrub: false,
};

export function getPolicy(profile: string): PolicyConfig {
  if (profile === 'strict') return STRICT_POLICY;
  return TRUSTED_POLICY;
}
