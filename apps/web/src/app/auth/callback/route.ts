import { NextResponse } from 'next/server';

import { readCookie } from '@/lib/cookies';
import { resolveHome } from '@/lib/identity';
import { PKCE_COOKIE, supabaseUrl } from '@/lib/oauth';
import { constantTimeEquals } from '@/lib/pkce';

function failure(request: Request, message: string): NextResponse {
  const target = new URL('/login', request.url);
  target.searchParams.set('error', message);
  const response = NextResponse.redirect(target);
  response.cookies.set(PKCE_COOKIE, '', { path: '/', maxAge: 0 });
  return response;
}

export async function GET(request: Request): Promise<NextResponse> {
  const url = new URL(request.url);
  const providerError = url.searchParams.get('error_description') ?? url.searchParams.get('error');
  if (providerError) return failure(request, providerError);

  const code = url.searchParams.get('code');
  if (!code) return failure(request, 'Google returned no authorisation code.');

  const stored = readCookie(request.headers.get('cookie'), PKCE_COOKIE);
  if (!stored) return failure(request, 'The sign-in request expired. Start again.');

  const [verifier, expectedState] = stored.split('.');
  if (!constantTimeEquals(url.searchParams.get('state') ?? undefined, expectedState)) {
    return failure(request, 'The sign-in response did not match the request.');
  }

  const base = supabaseUrl();
  const anonKey = process.env.SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!base || !anonKey) return failure(request, 'Supabase is not configured.');

  const exchange = await fetch(`${base}/auth/v1/token?grant_type=pkce`, {
    method: 'POST',
    headers: { apikey: anonKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({ auth_code: code, code_verifier: verifier }),
  });

  const payload = (await exchange.json().catch(() => ({}))) as {
    access_token?: string;
    expires_in?: number;
    msg?: string;
    error_description?: string;
  };

  if (!exchange.ok || !payload.access_token) {
    return failure(
      request,
      payload.msg ?? payload.error_description ?? `Google sign-in failed (${exchange.status}).`,
    );
  }

  // Clinic staff need an invitation; a pet parent may be brand new (spec 2.1), so an
  // unlinked Google identity is sent to finish its profile rather than turned away.
  let home: string | null = null;
  try {
    home = await resolveHome(payload.access_token);
  } catch {
    return failure(request, 'The API is unreachable, so the session could not be opened.');
  }

  const response = NextResponse.redirect(
    new URL(home ? '/enter' : '/portal/join', url.origin),
  );
  response.cookies.set('pc_token', payload.access_token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: payload.expires_in ?? 3600,
  });
  response.cookies.set(PKCE_COOKIE, '', { path: '/', maxAge: 0 });
  return response;
}
