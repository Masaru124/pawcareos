import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

/** The profile step of self-serve signup: name and WhatsApp number, nothing else. */
export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as {
    full_name?: string;
    phone?: string;
  };

  const response = await authorisedFetch('/api/v1/auth/parent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_name: (body.full_name ?? '').trim(),
      phone: (body.phone ?? '').trim(),
    }),
  });

  if (!response) {
    return Response.json({ error: 'Sign in again to finish setting up.' }, { status: 401 });
  }

  if (!response.ok) {
    const detail = apiDetail(await readJson(response), `Could not finish setup (${response.status}).`);
    return Response.json({ error: detail }, { status: response.status });
  }

  return Response.json({ ok: true });
}
