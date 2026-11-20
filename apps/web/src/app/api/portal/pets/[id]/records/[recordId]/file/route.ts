import { authorisedFetch } from '@/lib/session';

/** Stream an uploaded record back to the family that owns it. */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string; recordId: string }> },
) {
  const { id, recordId } = await params;
  const response = await authorisedFetch(`/api/v1/portal/pets/${id}/records/${recordId}/file`);

  if (!response) {
    return new Response('Sign in again to open this record.', { status: 401 });
  }

  const headers = new Headers();
  for (const header of ['content-type', 'content-disposition', 'content-length']) {
    const value = response.headers.get(header);
    if (value) headers.set(header, value);
  }

  return new Response(response.body, { status: response.status, headers });
}
