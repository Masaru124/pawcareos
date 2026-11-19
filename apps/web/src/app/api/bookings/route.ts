import { NextResponse } from 'next/server';

import { apiBase, apiDetail, readJson } from '@/lib/session';

export async function POST(request: Request): Promise<NextResponse> {
  const payload = await request.json().catch(() => null);
  if (!payload) {
    return NextResponse.json({ error: 'Send a booking body.' }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBase()}/api/v1/directory/bookings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json(
      { error: `The booking service at ${apiBase()} did not answer.` },
      { status: 502 },
    );
  }

  const body = await readJson(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: apiDetail(body, `Booking failed (${upstream.status}).`) },
      { status: upstream.status },
    );
  }
  return NextResponse.json({ ok: true, booking: body });
}
