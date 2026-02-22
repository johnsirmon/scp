import { Case } from '../core/types.js';

export interface StorageBackend {
  loadCases(): Promise<Record<string, Case>>;
  saveCases(cases: Record<string, Case>): Promise<void>;
  loadVault(): Promise<Record<string, Record<string, string>>>;
  saveVault(vault: Record<string, Record<string, string>>): Promise<void>;
}
