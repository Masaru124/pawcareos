import { NextResponse } from 'next/server';

import { apiBase, token } from '@/lib/session';

export async function POST(request: Request) {
  const accessToken = await token();
  if (!accessToken) {
    return NextResponse.json({ error: 'Sign in first.' }, { status: 401 });
  }

  const key = request.headers.get('Idempotency-Key');
  if (!key) {
    return NextResponse.json({ error: 'Idempotency-Key is required.' }, { status: 400 });
  }

  const body = await request.text();
  const response = await fetch(`${apiBase()}/api/v1/consults`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Idempotency-Key': key,
    },
    body,
    cache: 'no-store',
  });

  const payload = await response.text();
  return new NextResponse(payload, {
    status: response.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
