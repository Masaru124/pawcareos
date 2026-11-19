'use client';

import { useRouter } from 'next/navigation';
import { useState, useTransition } from 'react';

type Props = {
  id: string;
  status: string;
  desk?: boolean;
};

/**
 * One tap per state change. The API decides what is legal; this only offers the
 * transitions that match the current state so a button is never a lie.
 */
export function AppointmentActions({ id, status, desk = false }: Props) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function move(next: string) {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`/api/appointments/${id}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: next }),
      });
      const body = (await response.json().catch(() => ({}))) as { error?: string };
      if (!response.ok) {
        setError(body.error ?? 'That did not go through.');
        return;
      }
      startTransition(() => router.refresh());
    } catch {
      setError('The clinic server is unreachable.');
    } finally {
      setBusy(false);
    }
  }

  const disabled = busy || pending;

  return (
    <>
      {status === 'booked' && (
        <>
          <button
            type="button"
            className="button small"
            disabled={disabled}
            onClick={() => move('confirmed')}
          >
            {desk ? 'Check in' : 'Arrived'}
          </button>
          <button
            type="button"
            className="button danger tiny"
            disabled={disabled}
            onClick={() => move('cancelled')}
            aria-label="Cancel this appointment"
          >
            Cancel
          </button>
        </>
      )}

      {status === 'confirmed' && (
        <>
          <button
            type="button"
            className="button ghost small"
            disabled={disabled}
            onClick={() => move('completed')}
          >
            Mark seen
          </button>
          <button
            type="button"
            className="button danger tiny"
            disabled={disabled}
            onClick={() => move('cancelled')}
            aria-label="Cancel this appointment"
          >
            Cancel
          </button>
        </>
      )}

      {error && (
        <span role="alert" className="fine" style={{ color: 'var(--rose)', flexBasis: '100%' }}>
          {error}
        </span>
      )}
    </>
  );
}
