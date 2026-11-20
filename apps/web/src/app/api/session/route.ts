import { NextResponse } from 'next/server';

import { ensureParentProfile, invitationFor, resolveHome } from '@/lib/identity';

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

/**
 * Clinic staff still need an invitation before a session opens. A pet parent does not:
 * spec 2.1 lets them sign up first and attach to a clinic later. An identity with no
 * PawCare row yet keeps its cookie but is sent to finish their profile, where the API
 * refuses every clinic endpoint.
 */
async function openSession(accessToken: string, expiresIn?: number): Promise<NextResponse> {
  try {
    if ((await resolveHome(accessToken)) === null) {
      return withCookie(
        NextResponse.json({ ok: true, signedIn: true, next: '/portal/join' }),
        accessToken,
        expiresIn,
      );
    }
  } catch {
    return NextResponse.json(
      { error: 'PawCare could not reach its records, so the session was not opened. Try again.' },
      { status: 503 },
    );
  }
  return withCookie(NextResponse.json({ ok: true, signedIn: true }), accessToken, expiresIn);
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
    full_name?: string;
    phone?: string;
  };
  if (!body.email || !body.password) {
    return NextResponse.json({ error: 'Email and password are required.' }, { status: 400 });
  }
  if (body.mode === 'signup' && body.password.length < 6) {
    return NextResponse.json({ error: 'Use at least 6 characters.' }, { status: 400 });
  }

  if (body.mode === 'signup') {
    const fullName = (body.full_name ?? '').trim();
    const phone = (body.phone ?? '').trim();
    if (fullName.length < 2) {
      return NextResponse.json({ error: 'Enter your full name.' }, { status: 400 });
    }
    if (!/^\+[1-9]\d{9,14}$/.test(phone)) {
      return NextResponse.json(
        { error: 'Enter the WhatsApp number with country code, like +919876543210.' },
        { status: 400 },
      );
    }

    // A clinic invitation decides which door the new account opens; no invitation
    // means a self-serve pet-parent portal.
    let staffInvite = false;
    try {
      const invite = await invitationFor(body.email);
      staffInvite = invite.invited && invite.kind === 'clinic';
    } catch {
      return NextResponse.json(
        {
          error:
            'The invite list is unreachable, so no account was created. Try again in a moment.',
        },
        { status: 503 },
      );
    }

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
      if (staffInvite) return openSession(payload.access_token, payload.expires_in);
      try {
        const linked = await ensureParentProfile(payload.access_token, { full_name: fullName, phone });
        if (!linked) {
          return NextResponse.json(
            {
              error:
                'The account exists but the portal could not be opened. Sign in and finish your details.',
            },
            { status: 502 },
          );
        }
      } catch {
        return NextResponse.json(
          {
            error:
              'Your account was created, but PawCare could not reach its records. Sign in to finish setting up.',
          },
          { status: 503 },
        );
      }
      return openSession(payload.access_token, payload.expires_in);
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

  return openSession(payload.access_token, payload.expires_in);
}

export async function DELETE() {
  const result = NextResponse.json({ ok: true });
  result.cookies.set(COOKIE, '', { httpOnly: true, path: '/', maxAge: 0 });
  return result;
}
