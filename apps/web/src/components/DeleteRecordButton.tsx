'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function DeleteRecordButton({ petId, recordId }: { petId: string; recordId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function remove() {
    setBusy(true);
    setError(null);
    const response = await fetch(`/api/portal/pets/${petId}/records/${recordId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const payload = (await response.json().catch(() => ({}))) as { error?: string };
      setError(payload.error ?? `Could not delete this (${response.status}).`);
      setBusy(false);
      return;
    }
    router.refresh();
  }

  return (
    <span style={{ display: 'inline-flex', flexDirection: 'column', gap: 4 }}>
      <button
        type="button"
        className="button ghost tiny"
        onClick={remove}
        disabled={busy}
        aria-label="Delete this uploaded record"
      >
        {busy ? 'Removing…' : 'Delete'}
      </button>
      {error && (
        <span className="fine" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}
