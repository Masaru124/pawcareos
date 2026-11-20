'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

type Mode = 'signin' | 'signup';

export function LoginForm() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>('signin');
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function switchTo(next: Mode) {
    setMode(next);
    setError(null);
    setNotice(null);
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);

    const form = new FormData(event.currentTarget);
    const response = await fetch('/api/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: form.get('email'),
        password: form.get('password'),
        full_name: form.get('full_name'),
        phone: form.get('phone'),
        mode,
      }),
    });

    const payload = (await response.json().catch(() => ({}))) as {
      error?: string;
      message?: string;
      signedIn?: boolean;
      next?: string;
    };

    if (!response.ok) {
      setError(payload.error ?? `Sign in failed (${response.status}).`);
      setBusy(false);
      return;
    }

    if (payload.signedIn === false) {
      setNotice(payload.message ?? 'Confirm your address, then sign in.');
      setBusy(false);
      return;
    }

    router.replace(payload.next ?? '/enter');
    router.refresh();
  }

  const creating = mode === 'signup';

  return (
    <div className="stack">
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          type="button"
          className={creating ? 'button ghost' : 'button'}
          style={{ padding: '7px 14px' }}
          onClick={() => switchTo('signin')}
        >
          Sign in
        </button>
        <button
          type="button"
          className={creating ? 'button' : 'button ghost'}
          style={{ padding: '7px 14px' }}
          onClick={() => switchTo('signup')}
        >
          Create account
        </button>
      </div>

      {/* method=post so a submit before hydration cannot put the password in the URL. */}
      <form className="stack" onSubmit={submit} method="post">
        {creating && (
          <div className="field">
            <label htmlFor="full_name">Full name</label>
            <input id="full_name" name="full_name" required minLength={2} autoComplete="name" />
          </div>
        )}
        <div className="field">
          <label htmlFor="email">{creating ? 'Email' : 'Work email'}</label>
          <input id="email" name="email" type="email" autoComplete="username" required />
        </div>
        {creating && (
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
        )}
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete={creating ? 'new-password' : 'current-password'}
            minLength={creating ? 6 : undefined}
            required
          />
        </div>

        {error && (
          <p className="pill overdue" role="alert">
            {error}
          </p>
        )}
        {notice && (
          <p className="pill due_soon" role="status">
            {notice}
          </p>
        )}

        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Working…' : creating ? 'Create account' : 'Sign in'}
        </button>
        <p className="fine">
          {creating
            ? 'Pet parents can sign up here. Clinic staff need an invitation from their clinic first.'
            : 'Sessions last an hour. Clinic staff access needs an invitation on file.'}
        </p>
      </form>
    </div>
  );
}
