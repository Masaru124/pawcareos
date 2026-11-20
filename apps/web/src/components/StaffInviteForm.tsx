'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function StaffInviteForm() {
  const router = useRouter();
  const [role, setRole] = useState('receptionist');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // React nulls currentTarget once the handler awaits, so keep the node now.
    const formElement = event.currentTarget;
    setBusy(true);
    setError(null);
    setNotice(null);

    const form = new FormData(event.currentTarget);
    const response = await fetch('/api/admin/staff', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: form.get('full_name'),
        email: form.get('email'),
        role,
        vci_registration_no: form.get('vci') || null,
      }),
    });

    const payload = (await response.json().catch(() => ({}))) as {
      error?: string;
      staff?: { full_name: string; email: string };
    };

    if (!response.ok) {
      setError(payload.error ?? `The invitation failed (${response.status}).`);
      setBusy(false);
      return;
    }

    setNotice(`${payload.staff?.full_name ?? 'Your colleague'} can now sign in as ${payload.staff?.email}.`);
    setBusy(false);
    formElement.reset();
    // Refresh after the notice has rendered: an immediate refresh re-creates the
    // server tree and can wipe this component's state before anyone reads it.
    window.setTimeout(() => router.refresh(), 1200);
  }

  return (
    <form className="stack" onSubmit={submit}>
      <div className="field">
        <label htmlFor="full_name">Full name</label>
        <input id="full_name" name="full_name" required minLength={2} />
      </div>
      <div className="field">
        <label htmlFor="email">Work email</label>
        <input id="email" name="email" type="email" required />
      </div>
      <div className="field">
        <label htmlFor="role">Role</label>
        <select
          id="role"
          name="role"
          value={role}
          onChange={(event) => setRole(event.target.value)}
        >
          <option value="receptionist">Receptionist</option>
          <option value="doctor">Doctor</option>
          <option value="owner">Owner / admin</option>
        </select>
      </div>
      {role === 'doctor' && (
        <div className="field">
          <label htmlFor="vci">VCI registration number</label>
          <input id="vci" name="vci" required placeholder="KAR-12345" />
        </div>
      )}

      {error && (
        <p className="pill overdue" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="pill valid" role="status">
          {notice}
        </p>
      )}

      <button className="button" type="submit" disabled={busy}>
        {busy ? 'Inviting…' : 'Invite colleague'}
      </button>
      <p className="fine">The first verified sign-in with that address claims the invitation.</p>
    </form>
  );
}
