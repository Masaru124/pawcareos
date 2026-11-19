import { describe, expect, it } from 'vitest';

import { challengeFor, constantTimeEquals, createState, createVerifier } from '../src/lib/pkce';

describe('pkce', () => {
  it('produces a verifier inside the RFC 7636 charset', () => {
    for (let attempt = 0; attempt < 50; attempt += 1) {
      const verifier = createVerifier();
      expect(verifier.length).toBeGreaterThanOrEqual(43);
      expect(verifier.length).toBeLessThanOrEqual(128);
      expect(verifier).toMatch(/^[A-Za-z0-9\-._~]+$/);
    }
  });

  it('matches the RFC 7636 appendix B vector', () => {
    expect(challengeFor('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk')).toBe(
      'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM',
    );
  });

  it('never repeats a verifier or a state', () => {
    expect(new Set(Array.from({ length: 100 }, createVerifier)).size).toBe(100);
    expect(new Set(Array.from({ length: 100 }, createState)).size).toBe(100);
  });

  it('compares states without early exit', () => {
    expect(constantTimeEquals('abc', 'abc')).toBe(true);
    expect(constantTimeEquals('abc', 'abd')).toBe(false);
    expect(constantTimeEquals('abc', 'abcd')).toBe(false);
    expect(constantTimeEquals(undefined, 'abc')).toBe(false);
    expect(constantTimeEquals('abc', undefined)).toBe(false);
  });
});
