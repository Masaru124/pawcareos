import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { POST } from '../src/app/api/session/route';

const URL = 'https://demo.supabase.co';

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function request(payload: Record<string, unknown>): Request {
  return new Request('http://localhost/api/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

function stubFetch(response: Response) {
  const spy = vi.fn().mockResolvedValue(response);
  vi.stubGlobal('fetch', spy);
  return spy;
}

beforeEach(() => {
  vi.stubEnv('SUPABASE_URL', URL);
  vi.stubEnv('SUPABASE_ANON_KEY', 'anon-key');
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('sign in', () => {
  it('stores the token in an httpOnly cookie', async () => {
    const fetchSpy = stubFetch(json({ access_token: 'a.b.c', expires_in: 900 }));

    const response = await POST(request({ email: 'doc@clinic.test', password: 'secret1' }));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ok: true, signedIn: true });

    const cookie = response.headers.get('set-cookie') ?? '';
    expect(cookie).toContain('pc_token=a.b.c');
    expect(cookie.toLowerCase()).toContain('httponly');
    expect(cookie).toContain('Max-Age=900');

    const [url, init] = fetchSpy.mock.calls[0];
    expect(url).toBe(`${URL}/auth/v1/token?grant_type=password`);
    expect((init as RequestInit).headers).toMatchObject({ apikey: 'anon-key' });
  });

  it('explains wrong credentials instead of echoing the provider', async () => {
    stubFetch(json({ error_code: 'invalid_credentials', msg: 'Invalid login credentials' }, 400));

    const response = await POST(request({ email: 'doc@clinic.test', password: 'wrong' }));
    const body = await response.json();

    expect(response.status).toBe(401);
    expect(body.error).toBe('That email and password do not match an account.');
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it('names confirmation as the reason when the address is not confirmed', async () => {
    stubFetch(json({ error_code: 'email_not_confirmed', msg: 'Email not confirmed' }, 400));

    const response = await POST(request({ email: 'doc@clinic.test', password: 'secret1' }));

    expect(response.status).toBe(401);
    expect((await response.json()).error).toBe(
      'Confirm your email address first, then sign in.',
    );
  });

  it('passes through an unclassified provider message', async () => {
    stubFetch(json({ msg: 'Email rate limit exceeded' }, 429));

    const response = await POST(request({ email: 'doc@clinic.test', password: 'secret1' }));

    expect(response.status).toBe(401);
    expect((await response.json()).error).toBe('Email rate limit exceeded');
  });

  it('fails loudly when the provider returns no token', async () => {
    stubFetch(json({ ok: true }));

    const response = await POST(request({ email: 'doc@clinic.test', password: 'secret1' }));

    expect(response.status).toBe(502);
    expect((await response.json()).error).toBe('Supabase returned no token.');
  });
});

describe('sign up', () => {
  it('asks for confirmation when the provider returns no session', async () => {
    const fetchSpy = stubFetch(json({ id: 'user-1', email: 'new@clinic.test' }));

    const response = await POST(
      request({ email: 'new@clinic.test', password: 'secret1', mode: 'signup' }),
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.signedIn).toBe(false);
    expect(body.message).toContain('Confirm the address');
    expect(response.headers.get('set-cookie')).toBeNull();

    expect(fetchSpy.mock.calls[0][0]).toBe(`${URL}/auth/v1/signup`);
  });

  it('signs in directly when the project auto-confirms', async () => {
    stubFetch(json({ access_token: 'new.token', expires_in: 3600 }));

    const response = await POST(
      request({ email: 'new@clinic.test', password: 'secret1', mode: 'signup' }),
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ok: true, signedIn: true });
    expect(response.headers.get('set-cookie')).toContain('pc_token=new.token');
  });

  it('surfaces the provider reason for a rejected address', async () => {
    stubFetch(json({ code: 400, msg: 'Email address "x@example.com" is invalid' }, 400));

    const response = await POST(
      request({ email: 'x@example.com', password: 'secret1', mode: 'signup' }),
    );

    expect(response.status).toBe(400);
    expect((await response.json()).error).toBe('Email address "x@example.com" is invalid');
  });

  it('refuses a password shorter than six characters before calling out', async () => {
    const fetchSpy = stubFetch(json({}));

    const response = await POST(
      request({ email: 'new@clinic.test', password: 'abc', mode: 'signup' }),
    );

    expect(response.status).toBe(400);
    expect((await response.json()).error).toBe('Use at least 6 characters.');
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});

describe('credential handling', () => {
  it('reports a missing configuration instead of guessing', async () => {
    vi.stubEnv('SUPABASE_URL', '');
    vi.stubEnv('SUPABASE_ANON_KEY', '');
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', '');
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', '');

    const response = await POST(request({ email: 'a@b.test', password: 'secret1' }));

    expect(response.status).toBe(503);
    expect((await response.json()).error).toContain('SUPABASE_URL');
  });

  it('requires both fields', async () => {
    const response = await POST(request({ email: 'a@b.test' }));

    expect(response.status).toBe(400);
    expect((await response.json()).error).toBe('Email and password are required.');
  });
});
