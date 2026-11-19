import { NextResponse } from 'next/server';

const COOKIE = 'pc_token';

function supabase(): { url: string; anonKey: string } | null {
  const url = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) return null;
  return { url: url.replace(/\/$/, ''), anonKey };
}

type SupabaseError = {
  msg?: string;
  message?: string;
  error_description?: string;
  error?: string;
  error_code?: string;
};

/** Supabase puts the reason in a different field per endpoint; surface whichever exists. */
function reason(payload: SupabaseError, status: number): string {
  const text = payload.msg ?? payload.error_description ?? payload.message ?? payload.error;
  if (text) return text;
  return `Supabase refused the request (${status}).`;
}

function withCookie(response: NextResponse, accessToken: string, expiresIn?: number): NextResponse {
  response.cookies.set(COOKIE, accessToken, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: expiresIn ?? 3600,
  });
  return response;
}

export async function POST(request: Request) {
  const config = supabase();
  if (!config) {
    return NextResponse.json(
      { error: 'Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in apps/web/.env.local.' },
      { status: 503 },
    );
  }

  const body = (await request.json().catch(() => ({}))) as {
    email?: string;
    password?: string;
    mode?: 'signin' | 'signup';
  };
  if (!body.email || !body.password) {
    return NextResponse.json({ error: 'Email and password are required.' }, { status: 400 });
  }
  if (body.mode === 'signup' && body.password.length < 6) {
    return NextResponse.json({ error: 'Use at least 6 characters.' }, { status: 400 });
  }

  if (body.mode === 'signup') {
    const response = await fetch(`${config.url}/auth/v1/signup`, {
      method: 'POST',
      headers: { apikey: config.anonKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: body.email, password: body.password }),
    });
    const payload = (await response.json().catch(() => ({}))) as SupabaseError & {
      access_token?: string;
      expires_in?: number;
    };

    if (!response.ok) {
      return NextResponse.json({ error: reason(payload, response.status) }, { status: 400 });
    }
    if (payload.access_token) {
      return withCookie(NextResponse.json({ ok: true, signedIn: true }), payload.access_token, payload.expires_in);
    }
    return NextResponse.json({
      ok: true,
      signedIn: false,
      message: 'Account created. Confirm the address from the email we sent, then sign in.',
    });
  }

  const response = await fetch(`${config.url}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: { apikey: config.anonKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: body.email, password: body.password }),
  });
  const payload = (await response.json().catch(() => ({}))) as SupabaseError & {
    access_token?: string;
    expires_in?: number;
  };

  if (!response.ok) {
    const message =
      payload.error_code === 'invalid_credentials'
        ? 'That email and password do not match an account.'
        : payload.error_code === 'email_not_confirmed'
          ? 'Confirm your email address first, then sign in.'
          : reason(payload, response.status);
    return NextResponse.json({ error: message }, { status: 401 });
  }

  if (!payload.access_token) {
    return NextResponse.json({ error: 'Supabase returned no token.' }, { status: 502 });
  }

  return withCookie(NextResponse.json({ ok: true, signedIn: true }), payload.access_token, payload.expires_in);
}

export async function DELETE() {
  const result = NextResponse.json({ ok: true });
  result.cookies.set(COOKIE, '', { httpOnly: true, path: '/', maxAge: 0 });
  return result;
}
