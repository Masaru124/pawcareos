import { apiBase } from './session';

const CLINIC_HOME: Record<string, string> = {
  owner: '/admin',
  doctor: '/doctor',
  receptionist: '/frontdesk',
};

export const NOT_LINKED =
  "This address isn't linked to a clinic or pet record yet.";

/**
 * Open a pet-parent portal for a verified address (spec 2.1 self-serve signup).
 * Idempotent: the API returns the existing family when one is already attached.
 */
export async function ensureParentProfile(
  accessToken: string,
  profile: { full_name: string; phone: string },
): Promise<boolean> {
  const response = await fetch(`${apiBase()}/api/v1/auth/parent`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profile),
    cache: 'no-store',
  });
  if (response.status >= 500) throw new Error(`Parent signup failed (${response.status})`);
  return response.ok;
}

/**
 * Which door this verified session opens. The API decides; the web only routes.
 * A 5xx is not "unlinked": it must not cost a valid user their session.
 */
export async function resolveHome(accessToken: string): Promise<string | null> {
  const init = {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: 'no-store' as const,
  };

  const clinic = await fetch(`${apiBase()}/api/v1/auth/me`, init);
  if (clinic.status >= 500) throw new Error(`Clinic identity failed (${clinic.status})`);
  if (clinic.ok) {
    const me = (await clinic.json().catch(() => ({}))) as { role?: string };
    const home = CLINIC_HOME[me.role ?? ''];
    if (home) return home;
  }

  const parent = await fetch(`${apiBase()}/api/v1/portal/me`, init);
  if (parent.status >= 500) throw new Error(`Parent identity failed (${parent.status})`);
  return parent.ok ? '/portal' : null;
}

/** Sign-up gate: ask the API whether this address is on a clinic's invite list. */
export async function invitationFor(
  email: string,
): Promise<{ invited: boolean; kind?: string | null }> {
  const response = await fetch(`${apiBase()}/api/v1/auth/invitation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
    cache: 'no-store',
  });
  if (!response.ok) throw new Error(`Invitation lookup failed (${response.status})`);
  return (await response.json()) as { invited: boolean; kind?: string | null };
}
