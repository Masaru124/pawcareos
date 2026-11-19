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
        mode,
      }),
    });

    const payload = (await response.json().catch(() => ({}))) as {
      error?: string;
      message?: string;
      signedIn?: boolean;
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

    router.replace('/enter');
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

      <form className="stack" onSubmit={submit}>
        <div className="field">
          <label htmlFor="email">Work email</label>
          <input id="email" name="email" type="email" autoComplete="username" required />
        </div>
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
            ? 'Use the address your clinic invited. The first sign-in claims that invitation.'
            : 'Sessions last an hour and live in an httpOnly cookie.'}
        </p>
      </form>
    </div>
  );
}
