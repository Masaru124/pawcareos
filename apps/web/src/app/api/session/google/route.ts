import { NextResponse } from 'next/server';

import { browserOrigin, PKCE_COOKIE, supabaseUrl } from '@/lib/oauth';
import { challengeFor, createState, createVerifier } from '@/lib/pkce';

function back(request: Request, message: string): NextResponse {
  const target = new URL('/login', request.url);
  target.searchParams.set('error', message);
  return NextResponse.redirect(target);
}

export function GET(request: Request): NextResponse {
  const base = supabaseUrl();
  if (!base) {
    return back(request, 'Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.');
  }

  const verifier = createVerifier();
  const state = createState();

  const authorize = new URL(`${base}/auth/v1/authorize`);
  authorize.searchParams.set('provider', 'google');
  authorize.searchParams.set('redirect_to', `${browserOrigin(request)}/auth/callback`);
  authorize.searchParams.set('code_challenge', challengeFor(verifier));
  authorize.searchParams.set('code_challenge_method', 'S256');
  authorize.searchParams.set('flow_type', 'pkce');
  authorize.searchParams.set('state', state);

  const response = NextResponse.redirect(authorize);
  response.cookies.set(PKCE_COOKIE, `${verifier}.${state}`, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 600,
  });
  return response;
}
