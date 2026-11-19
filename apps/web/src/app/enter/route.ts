import { NextResponse } from 'next/server';

import { readCookie } from '@/lib/cookies';
import { apiBase, TOKEN_COOKIE } from '@/lib/session';

/**
 * One sign-in serves two populations. The API decides which: a clinic user answers
 * /auth/me, a pet parent answers /portal/me, and nobody else gets in.
 */
export async function GET(request: Request): Promise<NextResponse> {
  const accessToken = readCookie(request.headers.get('cookie'), TOKEN_COOKIE);
  const login = new URL('/login', request.url);
  if (!accessToken) return NextResponse.redirect(login);

  const headers = { Authorization: `Bearer ${accessToken}` };
  const options = { headers, cache: 'no-store' as const };

  try {
    const clinic = await fetch(`${apiBase()}/api/v1/auth/me`, options);
    if (clinic.ok) {
      const me = (await clinic.json().catch(() => ({}))) as { role?: string };
      const homes: Record<string, string> = {
        owner: '/admin',
        doctor: '/doctor',
        receptionist: '/frontdesk',
      };
      return NextResponse.redirect(new URL(homes[me.role ?? ''] ?? '/login', request.url));
    }

    const parent = await fetch(`${apiBase()}/api/v1/portal/me`, options);
    if (parent.ok) return NextResponse.redirect(new URL('/portal', request.url));

    login.searchParams.set(
      'error',
      'Signed in, but neither a clinic user nor a pet profile matches this address yet.',
    );
    return NextResponse.redirect(login);
  } catch {
    login.searchParams.set('error', 'The API is unreachable, so the session could not be routed.');
    return NextResponse.redirect(login);
  }
}
