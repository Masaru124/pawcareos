import { NextResponse } from 'next/server';

import { readCookie } from '@/lib/cookies';
import { resolveHome } from '@/lib/identity';
import { TOKEN_COOKIE } from '@/lib/session';

/**
 * One sign-in serves two populations. The API decides which: a clinic user answers
 * /auth/me, a pet parent answers /portal/me. A verified address with no PawCare row
 * yet is a new pet parent finishing signup, so it goes to the profile step.
 */
export async function GET(request: Request): Promise<NextResponse> {
  const accessToken = readCookie(request.headers.get('cookie'), TOKEN_COOKIE);
  const login = new URL('/login', request.url);
  if (!accessToken) return NextResponse.redirect(login);

  try {
    const home = await resolveHome(accessToken);
    if (home) return NextResponse.redirect(new URL(home, request.url));

    return NextResponse.redirect(new URL('/portal/join', request.url));
  } catch {
    login.searchParams.set('error', 'The API is unreachable, so the session could not be routed.');
    return NextResponse.redirect(login);
  }
}
