import { NextResponse } from 'next/server';

import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

export async function POST(request: Request): Promise<NextResponse> {
  const payload = await request.json().catch(() => null);
  if (!payload) {
    return NextResponse.json({ error: 'Send the colleague details.' }, { status: 400 });
  }

  const upstream = await authorisedFetch('/api/v1/admin/staff', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!upstream) {
    return NextResponse.json({ error: 'Sign in first.' }, { status: 401 });
  }

  const body = await readJson(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: apiDetail(body, `The invitation failed (${upstream.status}).`) },
      { status: upstream.status },
    );
  }
  return NextResponse.json({ ok: true, staff: body });
}
