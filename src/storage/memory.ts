import { Case } from '../core/types.js';
import { StorageBackend } from './types.js';

export class MemoryStorage implements StorageBackend {
  private cases: Record<string, Case> = {};
  private vault: Record<string, Record<string, string>> = {};

  async loadCases(): Promise<Record<string, Case>> {
    return { ...this.cases };
  }

  async saveCases(cases: Record<string, Case>): Promise<void> {
    this.cases = { ...cases };
  }

  async loadVault(): Promise<Record<string, Record<string, string>>> {
    return { ...this.vault };
  }

  async saveVault(vault: Record<string, Record<string, string>>): Promise<void> {
    this.vault = { ...vault };
  }
}
