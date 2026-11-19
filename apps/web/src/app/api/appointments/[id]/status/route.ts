import { NextResponse } from 'next/server';

import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

/** The desk's one write: move an appointment along its day. */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<NextResponse> {
  const { id } = await params;
  const payload = (await request.json().catch(() => null)) as { status?: string } | null;
  if (!payload?.status) {
    return NextResponse.json({ error: 'Pick the next state.' }, { status: 400 });
  }

  const upstream = await authorisedFetch(`/api/v1/appointments/${id}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: payload.status }),
  });
  if (!upstream) {
    return NextResponse.json({ error: 'Sign in first.' }, { status: 401 });
  }

  const body = await readJson(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: apiDetail(body, `That change failed (${upstream.status}).`) },
      { status: upstream.status },
    );
  }
  return NextResponse.json({ ok: true, appointment: body });
}
