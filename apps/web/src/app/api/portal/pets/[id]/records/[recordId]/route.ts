import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

/** Withdraw a file the family uploaded themselves. */
export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string; recordId: string }> },
) {
  const { id, recordId } = await params;
  const response = await authorisedFetch(`/api/v1/portal/pets/${id}/records/${recordId}`, {
    method: 'DELETE',
  });

  if (!response) {
    return Response.json({ error: 'Sign in again to change this record.' }, { status: 401 });
  }
  if (!response.ok) {
    const detail = apiDetail(await readJson(response), `Could not delete (${response.status}).`);
    return Response.json({ error: detail }, { status: response.status });
  }

  return new Response(null, { status: 204 });
}
