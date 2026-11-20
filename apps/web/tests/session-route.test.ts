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

type Replies = {
  token?: Response;
  signup?: Response;
  invitation?: Response;
  clinic?: Response;
  parent?: Response;
  parentSignup?: Response;
};

const NEW_PARENT = {
  email: 'new@example.com',
  password: 'secret1',
  full_name: 'Anita Rao',
  phone: '+919876543210',
  mode: 'signup' as const,
};

/** Answers per endpoint, so the identity gate is exercised, not short-circuited. */
function stubFetch(replies: Replies) {
  const spy = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
    const url = String(input);
    if (url.includes('/api/v1/auth/invitation')) return replies.invitation ?? json({ invited: true, kind: 'clinic' });
    if (url.includes('/api/v1/auth/parent')) return replies.parentSignup ?? json({ created: true });
    if (url.includes('/auth/v1/signup')) return replies.signup ?? json({});
    if (url.includes('/auth/v1/token')) return replies.token ?? json({ access_token: 'a.b.c', expires_in: 900 });
    if (url.includes('/api/v1/auth/me')) return replies.clinic ?? json({ role: 'doctor' });
    if (url.includes('/api/v1/portal/me')) return replies.parent ?? json({}, 401);
    return json({}, 404);
  });
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
    const fetchSpy = stubFetch({ token: json({ access_token: 'a.b.c', expires_in: 900 }) });

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

  it('sends a verified address with no PawCare row to finish its profile', async () => {
    stubFetch({
      token: json({ access_token: 'orphan.token' }),
      clinic: json({}, 401),
      parent: json({}, 401),
    });

    const response = await POST(request({ email: 'stranger@example.com', password: 'secret1' }));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ok: true, signedIn: true, next: '/portal/join' });
    expect(response.headers.get('set-cookie')).toContain('pc_token=orphan.token');
  });

  it('explains wrong credentials instead of echoing the provider', async () => {
    stubFetch({ token: json({ error_code: 'invalid_credentials', msg: 'Invalid login credentials' }, 400) });

    const response = await POST(request({ email: 'doc@clinic.test', password: 'wrong' }));
    const body = await response.json();

    expect(response.status).toBe(401);
    expect(body.error).toBe('That email and password do not match an account.');
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it('names confirmation as the reason when the address is not confirmed', async () => {
    stubFetch({ token: json({ error_code: 'email_not_confirmed', msg: 'Email not confirmed' }, 400) });

    const response = await POST(request({ email: 'doc@clinic.test', password: 'secret1' }));

    expect(response.status).toBe(401);
    expect((await response.json()).error).toBe(
      'Confirm your email address first, then sign in.',
    );
  });

  it('passes through an unclassified provider message', async () => {
    stubFetch({ token: json({ msg: 'Email rate limit exceeded' }, 429) });

    const response = await POST(request({ email: 'doc@clinic.test', password: 'secret1' }));

    expect(response.status).toBe(401);
    expect((await response.json()).error).toBe('Email rate limit exceeded');
  });

  it('fails loudly when the provider returns no token', async () => {
    stubFetch({ token: json({ ok: true }) });

    const response = await POST(request({ email: 'doc@clinic.test', password: 'secret1' }));

    expect(response.status).toBe(502);
    expect((await response.json()).error).toBe('Supabase returned no token.');
  });
});

describe('sign up', () => {
  it('asks for confirmation when the provider returns no session', async () => {
    const fetchSpy = stubFetch({ signup: json({ id: 'user-1', email: 'new@clinic.test' }) });

    const response = await POST(request({ ...NEW_PARENT }));
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.signedIn).toBe(false);
    expect(body.message).toContain('Confirm the address');
    expect(response.headers.get('set-cookie')).toBeNull();

    expect(fetchSpy.mock.calls.map(([url]) => String(url))).toEqual([
      'http://127.0.0.1:8000/api/v1/auth/invitation',
      `${URL}/auth/v1/signup`,
    ]);
  });

  it('signs an uninvited address up as a self-serve pet parent', async () => {
    const fetchSpy = stubFetch({
      invitation: json({ invited: false, kind: null }),
      signup: json({ access_token: 'parent.token', expires_in: 3600 }),
      clinic: json({}, 401),
      parent: json({ parent_name: 'Anita Rao', pets: [] }),
    });

    const response = await POST(request({ ...NEW_PARENT }));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ok: true, signedIn: true });
    expect(response.headers.get('set-cookie')).toContain('pc_token=parent.token');

    const urls = fetchSpy.mock.calls.map(([url]) => String(url));
    expect(urls).toContain(`${URL}/auth/v1/signup`);
    expect(urls).toContain('http://127.0.0.1:8000/api/v1/auth/parent');
  });

  it('does not create a parent profile for invited clinic staff', async () => {
    const fetchSpy = stubFetch({
      invitation: json({ invited: true, kind: 'clinic' }),
      signup: json({ access_token: 'staff.token', expires_in: 3600 }),
      clinic: json({ role: 'doctor' }),
    });

    await POST(request({ ...NEW_PARENT, email: 'doc@clinic.test' }));

    expect(fetchSpy.mock.calls.map(([url]) => String(url))).not.toContain(
      'http://127.0.0.1:8000/api/v1/auth/parent',
    );
  });

  it('creates nothing when the invite list cannot be reached', async () => {
    const fetchSpy = stubFetch({ invitation: json({}, 500) });

    const response = await POST(request({ ...NEW_PARENT }));

    expect(response.status).toBe(503);
    expect((await response.json()).error).toContain('invite list is unreachable');
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it('signs in directly when the project auto-confirms', async () => {
    stubFetch({
      signup: json({ access_token: 'new.token', expires_in: 3600 }),
      clinic: json({ role: 'receptionist' }),
    });

    const response = await POST(request({ ...NEW_PARENT, email: 'new@clinic.test' }));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ok: true, signedIn: true });
    expect(response.headers.get('set-cookie')).toContain('pc_token=new.token');
  });

  it('surfaces the provider reason for a rejected address', async () => {
    stubFetch({ signup: json({ code: 400, msg: 'Email address "x@example.com" is invalid' }, 400) });

    const response = await POST(request({ ...NEW_PARENT, email: 'x@example.com' }));

    expect(response.status).toBe(400);
    expect((await response.json()).error).toBe('Email address "x@example.com" is invalid');
  });

  it('refuses a password shorter than six characters before calling out', async () => {
    const fetchSpy = stubFetch({});

    const response = await POST(
      request({ ...NEW_PARENT, email: 'new@clinic.test', password: 'abc' }),
    );

    expect(response.status).toBe(400);
    expect((await response.json()).error).toBe('Use at least 6 characters.');
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('asks for a name and a country-code number before calling out', async () => {
    const fetchSpy = stubFetch({});

    const noName = await POST(request({ ...NEW_PARENT, full_name: ' ' }));
    expect(noName.status).toBe(400);
    expect((await noName.json()).error).toBe('Enter your full name.');

    const badPhone = await POST(request({ ...NEW_PARENT, phone: '9876543210' }));
    expect(badPhone.status).toBe(400);
    expect((await badPhone.json()).error).toContain('country code');

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
