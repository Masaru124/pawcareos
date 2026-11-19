import { cookies } from 'next/headers';

export const TOKEN_COOKIE = 'pc_token';

export function apiBase(): string {
  return process.env.PAWCARE_API_URL ?? 'http://127.0.0.1:8000';
}

export async function token(): Promise<string | null> {
  const store = await cookies();
  return store.get(TOKEN_COOKIE)?.value ?? null;
}

/** The email inside the token, for display only: the API is what verifies it. */
export async function sessionEmail(): Promise<string | null> {
  const raw = await token();
  if (!raw) return null;
  try {
    const part = raw.split('.')[1];
    const payload = JSON.parse(Buffer.from(part, 'base64url').toString('utf8')) as {
      email?: string;
    };
    return payload.email ?? null;
  } catch {
    return null;
  }
}

export async function authorisedFetch(path: string, init?: RequestInit): Promise<Response | null> {
  const accessToken = await token();
  if (!accessToken) return null;
  return fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      Authorization: `Bearer ${accessToken}`,
    },
    cache: 'no-store',
  });
}

export async function publicFetch(path: string): Promise<Response> {
  return fetch(`${apiBase()}${path}`, { cache: 'no-store' });
}

/** Turn a FastAPI error body into something worth showing a human. */
export function apiDetail(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object') return fallback;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: string; loc?: unknown[] } | undefined;
    if (first?.msg) {
      const field = Array.isArray(first.loc) ? first.loc.slice(1).join('.') : '';
      const message = first.msg.replace('Value error, ', '');
      return field ? `${field}: ${message}` : message;
    }
  }
  return fallback;
}

export async function readJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null);
}
