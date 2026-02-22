import { z } from 'zod';

export const PolicyProfileSchema = z.enum(['strict', 'trusted']);
export type PolicyProfile = z.infer<typeof PolicyProfileSchema>;

export interface PolicyConfig {
  profile: PolicyProfile;
  requireRedaction: boolean;
  allowFullRehydration: boolean;
  encryptVault: boolean;
  auditLog: boolean;
  outboundScrub: boolean;
}
