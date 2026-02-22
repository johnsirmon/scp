import { describe, it, expect } from 'vitest';
import { randomBytes } from 'node:crypto';
import { encrypt, decrypt } from '../src/storage/crypto.js';

describe('AES-256-GCM crypto', () => {
  const key = randomBytes(32).toString('hex');

  it('encrypts and decrypts text correctly', () => {
    const plaintext = 'Hello, secret world!';
    const ciphertext = encrypt(plaintext, key);
    expect(ciphertext).not.toBe(plaintext);
    const decrypted = decrypt(ciphertext, key);
    expect(decrypted).toBe(plaintext);
  });

  it('produces unique ciphertext each time (random IV)', () => {
    const plaintext = 'same text';
    const c1 = encrypt(plaintext, key);
    const c2 = encrypt(plaintext, key);
    expect(c1).not.toBe(c2);
  });

  it('fails to decrypt with wrong key', () => {
    const ciphertext = encrypt('secret', key);
    const wrongKey = randomBytes(32).toString('hex');
    expect(() => decrypt(ciphertext, wrongKey)).toThrow();
  });

  it('rejects malformed ciphertext', () => {
    expect(() => decrypt('bad:data', key)).toThrow();
  });
});
