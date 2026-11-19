import { NextResponse } from 'next/server';

export function GET(request: Request) {
  const response = NextResponse.redirect(new URL('/login', request.url));
  response.cookies.set('pc_token', '', { httpOnly: true, path: '/', maxAge: 0 });
  return response;
}
