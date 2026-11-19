import { createHash, randomBytes } from 'node:crypto';

/** RFC 7636 code verifier: 43-128 characters from the unreserved set. */
export function createVerifier(bytes = 32): string {
  return randomBytes(bytes).toString('base64url');
}

/** S256 challenge: base64url(sha256(verifier)). */
export function challengeFor(verifier: string): string {
  return createHash('sha256').update(verifier).digest('base64url');
}

export function createState(): string {
  return randomBytes(16).toString('base64url');
}

export function constantTimeEquals(left: string | undefined, right: string | undefined): boolean {
  if (!left || !right || left.length !== right.length) return false;
  let mismatch = 0;
  for (let index = 0; index < left.length; index += 1) {
    mismatch |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return mismatch === 0;
}
