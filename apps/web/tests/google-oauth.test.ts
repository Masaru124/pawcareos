import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { GET as authorize } from '../src/app/api/session/google/route';
import { GET as callback } from '../src/app/auth/callback/route';

const BASE = 'https://demo.supabase.co';

function request(path: string, cookie?: string, host?: string): Request {
  return new Request(`http://localhost:3000${path}`, {
    headers: {
      ...(cookie ? { cookie } : {}),
      ...(host ? { host } : {}),
    },
  });
}

beforeEach(() => {
  vi.stubEnv('SUPABASE_URL', BASE);
  vi.stubEnv('SUPABASE_ANON_KEY', 'anon-key');
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('starting a Google sign-in', () => {
  it('redirects to Supabase with an S256 challenge and a state', () => {
    const response = authorize(request('/api/session/google'));

    expect(response.status).toBe(307);
    const location = new URL(response.headers.get('location') ?? '');
    expect(location.origin + location.pathname).toBe(`${BASE}/auth/v1/authorize`);
    expect(location.searchParams.get('provider')).toBe('google');
    expect(location.searchParams.get('code_challenge_method')).toBe('S256');
    expect(location.searchParams.get('flow_type')).toBe('pkce');
    expect(location.searchParams.get('code_challenge')).toMatch(/^[A-Za-z0-9\-_]{43}$/);
    expect(location.searchParams.get('state')).toBeTruthy();
    expect(location.searchParams.get('redirect_to')).toBe('http://localhost:3000/auth/callback');
  });

  it('stores the verifier and state in an httpOnly cookie', () => {
    const response = authorize(request('/api/session/google'));
    const cookie = response.headers.get('set-cookie') ?? '';

    expect(cookie).toContain('pc_pkce=');
    expect(cookie.toLowerCase()).toContain('httponly');
    expect(cookie).toContain('Max-Age=600');
    expect(cookie).not.toContain('pc_token');
  });

  it('returns the browser to the host it started on, not the dev server host', () => {
    const response = authorize(request('/api/session/google', undefined, '127.0.0.1:3000'));
    const location = new URL(response.headers.get('location') ?? '');

    expect(location.searchParams.get('redirect_to')).toBe('http://127.0.0.1:3000/auth/callback');
  });

  it('returns to the form with a reason when Supabase is not configured', () => {
    vi.stubEnv('SUPABASE_URL', '');
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', '');

    const response = authorize(request('/api/session/google'));

    expect(response.headers.get('location')).toContain('/login?error=Supabase+is+not+configured');
  });
});

describe('the callback', () => {
  it('explains a provider error instead of crashing', async () => {
    const response = await callback(
      request('/auth/callback?error=access_denied&error_description=The+user+denied+access'),
    );

    expect(response.headers.get('location')).toContain(
      '/login?error=The+user+denied+access',
    );
  });

  it('refuses a callback with no code', async () => {
    const response = await callback(request('/auth/callback'));
    expect(response.headers.get('location')).toContain('/login?error=Google+returned+no');
  });

  it('refuses a callback with no stored verifier', async () => {
    const response = await callback(request('/auth/callback?code=abc&state=xyz'));
    expect(response.headers.get('location')).toContain('/login?error=The+sign-in+request+expired');
  });

  it('refuses a mismatched state', async () => {
    const response = await callback(
      request('/auth/callback?code=abc&state=wrong', 'pc_pkce=verifier.expected'),
    );
    expect(response.headers.get('location')).toContain(
      '/login?error=The+sign-in+response+did+not+match',
    );
  });

  it('exchanges the code and issues the session cookie', async () => {
    const fetchSpy = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ access_token: 'google.token', expires_in: 3600 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchSpy);

    const response = await callback(
      request('/auth/callback?code=the-code&state=the-state', 'pc_pkce=the-verifier.the-state'),
    );

    expect(response.headers.get('location')).toBe('http://localhost:3000/enter');
    const cookie = response.headers.get('set-cookie') ?? '';
    expect(cookie).toContain('pc_token=google.token');

    const [url, init] = fetchSpy.mock.calls[0];
    expect(url).toBe(`${BASE}/auth/v1/token?grant_type=pkce`);
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      auth_code: 'the-code',
      code_verifier: 'the-verifier',
    });
  });

  it('surfaces a failed exchange', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ msg: 'invalid flow state' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    const response = await callback(
      request('/auth/callback?code=stale&state=s', 'pc_pkce=v.s'),
    );

    expect(response.headers.get('location')).toContain('/login?error=invalid+flow+state');
  });
});
