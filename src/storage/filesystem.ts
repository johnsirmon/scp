import { readFileSync, writeFileSync, existsSync, mkdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { Case } from '../core/types.js';
import { StorageBackend } from './types.js';
import { encrypt, decrypt } from './crypto.js';

export class FilesystemStorage implements StorageBackend {
  private dataPath: string;
  private casesFile: string;
  private vaultFile: string;
  private keyFile: string;
  private vaultKey: string;

  constructor(dataPath: string) {
    this.dataPath = dataPath;
    this.casesFile = join(dataPath, 'cases.json');
    this.vaultFile = join(dataPath, 'vault.enc');
    this.keyFile = join(dataPath, '.key');
    this.ensureDataDir();
    this.vaultKey = this.getOrCreateKey();
  }

  private ensureDataDir(): void {
    if (!existsSync(this.dataPath)) {
      mkdirSync(this.dataPath, { recursive: true });
    }
  }

  private getOrCreateKey(): string {
    if (existsSync(this.keyFile)) {
      return readFileSync(this.keyFile, 'utf8').trim();
    }
    const key = randomBytes(32).toString('hex');
    writeFileSync(this.keyFile, key, { mode: 0o600 });
    return key;
  }

  async loadCases(): Promise<Record<string, Case>> {
    try {
      if (existsSync(this.casesFile)) {
        return JSON.parse(readFileSync(this.casesFile, 'utf8')) as Record<string, Case>;
      }
    } catch {
      console.warn('Warning: Could not load cases file, starting fresh');
    }
    return {};
  }

  async saveCases(cases: Record<string, Case>): Promise<void> {
    writeFileSync(this.casesFile, JSON.stringify(cases, null, 2));
  }

  async loadVault(): Promise<Record<string, Record<string, string>>> {
    try {
      if (existsSync(this.vaultFile)) {
        const encrypted = readFileSync(this.vaultFile, 'utf8').trim();
        return JSON.parse(decrypt(encrypted, this.vaultKey)) as Record<string, Record<string, string>>;
      }
    } catch {
      console.warn('Warning: Could not load vault, starting fresh');
    }
    return {};
  }

  async saveVault(vault: Record<string, Record<string, string>>): Promise<void> {
    const encrypted = encrypt(JSON.stringify(vault), this.vaultKey);
    writeFileSync(this.vaultFile, encrypted, { mode: 0o600 });
  }

  getDataSize(): number {
    try {
      return existsSync(this.casesFile) ? statSync(this.casesFile).size : 0;
    } catch {
      return 0;
    }
  }
}
