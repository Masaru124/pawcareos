'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function ParentJoinForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    const response = await fetch('/api/parent/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: form.get('full_name'),
        phone: form.get('phone'),
      }),
    });
    const payload = (await response.json().catch(() => ({}))) as { error?: string };

    if (!response.ok) {
      setError(payload.error ?? `Could not finish setup (${response.status}).`);
      setBusy(false);
      return;
    }

    router.replace('/portal');
    router.refresh();
  }

  return (
    <form className="stack" onSubmit={submit}>
      <div className="field">
        <label htmlFor="full_name">Full name</label>
        <input id="full_name" name="full_name" required minLength={2} autoComplete="name" />
      </div>
      <div className="field">
        <label htmlFor="phone">WhatsApp number</label>
        <input
          id="phone"
          name="phone"
          required
          pattern="^\+[1-9][0-9]{9,14}$"
          placeholder="+919876543210"
          autoComplete="tel"
        />
      </div>

      {error && (
        <p className="pill overdue" role="alert">
          {error}
        </p>
      )}

      <button className="button" type="submit" disabled={busy}>
        {busy ? 'Saving…' : 'Open my portal'}
      </button>
      <p className="fine">
        If your clinic already has this number on file, your pets and their records come with it.
      </p>
    </form>
  );
}
