import { NextResponse } from 'next/server';

import { readCookie } from '@/lib/cookies';
import { NOT_LINKED, resolveHome } from '@/lib/identity';
import { TOKEN_COOKIE } from '@/lib/session';

/**
 * One sign-in serves two populations. The API decides which: a clinic user answers
 * /auth/me, a pet parent answers /portal/me, and nobody else gets in.
 */
export async function GET(request: Request): Promise<NextResponse> {
  const accessToken = readCookie(request.headers.get('cookie'), TOKEN_COOKIE);
  const login = new URL('/login', request.url);
  if (!accessToken) return NextResponse.redirect(login);

  try {
    const home = await resolveHome(accessToken);
    if (home) return NextResponse.redirect(new URL(home, request.url));

    // Strict: an unlinked identity keeps no local session, so /login cannot bounce back here.
    login.searchParams.set('error', NOT_LINKED);
    const response = NextResponse.redirect(login);
    response.cookies.set(TOKEN_COOKIE, '', { httpOnly: true, path: '/', maxAge: 0 });
    return response;
  } catch {
    login.searchParams.set('error', 'The API is unreachable, so the session could not be routed.');
    return NextResponse.redirect(login);
  }
}
