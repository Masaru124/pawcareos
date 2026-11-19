/** Shared by the OAuth route and its callback: a route may only export handlers. */

export const PKCE_COOKIE = 'pc_pkce';

export function supabaseUrl(): string | null {
  const url = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  return url ? url.replace(/\/$/, '') : null;
}

/**
 * The origin the browser is actually on. Next can normalise request.url to the
 * dev server host, and the PKCE cookie belongs to the host the user started on.
 */
export function browserOrigin(request: Request): string {
  const url = new URL(request.url);
  const host = request.headers.get('host');
  return host ? `${url.protocol}//${host}` : url.origin;
}
