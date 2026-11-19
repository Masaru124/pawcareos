import { authorisedFetch } from './session';

export type ClinicRole = 'owner' | 'doctor' | 'receptionist';

/** Each role lands somewhere built for its own questions, not on a shared board. */
export const ROLE_HOME: Record<ClinicRole, string> = {
  owner: '/admin',
  doctor: '/doctor',
  receptionist: '/frontdesk',
};

export const ROLE_LABEL: Record<ClinicRole, string> = {
  owner: 'Owner',
  doctor: 'Doctor',
  receptionist: 'Front desk',
};

export type Principal =
  | { kind: 'clinic'; role: ClinicRole; name: string; label: string; home: string }
  | { kind: 'parent'; role: 'parent'; name: string; label: string; home: '/portal' };

function isClinicRole(value: unknown): value is ClinicRole {
  return value === 'owner' || value === 'doctor' || value === 'receptionist';
}

/**
 * Resolve the signed-in person once, on the server. The API is the authority:
 * a clinic user answers /auth/me, a pet parent answers /portal/me.
 */
export async function currentPrincipal(): Promise<Principal | null> {
  const me = await authorisedFetch('/api/v1/auth/me');
  if (me?.ok) {
    const body = (await me.json().catch(() => ({}))) as { role?: unknown; full_name?: string };
    if (isClinicRole(body.role)) {
      return {
        kind: 'clinic',
        role: body.role,
        name: body.full_name ?? 'Clinic user',
        label: ROLE_LABEL[body.role],
        home: ROLE_HOME[body.role],
      };
    }
  }

  const parent = await authorisedFetch('/api/v1/portal/me');
  if (parent?.ok) {
    const body = (await parent.json().catch(() => ({}))) as { parent_name?: string };
    return {
      kind: 'parent',
      role: 'parent',
      name: body.parent_name ?? 'Pet parent',
      label: 'Pet parent',
      home: '/portal',
    };
  }

  return null;
}
