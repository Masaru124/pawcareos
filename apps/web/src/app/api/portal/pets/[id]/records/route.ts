import { authorisedFetch } from '@/lib/session';

/** Forward a parent's upload to the API with the session its cookie carries. */
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = await request.formData();
  const response = await authorisedFetch(`/api/v1/portal/pets/${id}/records`, {
    method: 'POST',
    body,
  });

  if (!response) {
    return Response.json({ detail: 'Sign in again to upload records.' }, { status: 401 });
  }

  return new Response(await response.text(), {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') ?? 'application/json' },
  });
}
