'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

const TYPES = [
  { value: 'VACCINE_CARD', label: 'Vaccine card' },
  { value: 'EXTERNAL_RX', label: "Another clinic's prescription" },
  { value: 'LAB_REPORT', label: 'Lab report' },
  { value: 'XRAY', label: 'X-ray or scan' },
  { value: 'OTHER', label: 'Something else' },
];

export function LegacyRecordUpload({ petId }: { petId: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setBusy(true);
    setError(null);
    setNotice(null);

    const response = await fetch(`/api/portal/pets/${petId}/records`, {
      method: 'POST',
      body: new FormData(event.currentTarget),
    });
    const payload = (await response.json().catch(() => ({}))) as {
      detail?: string;
      record_type?: string;
    };

    if (!response.ok) {
      setError(payload.detail ?? `The upload failed (${response.status}).`);
      setBusy(false);
      return;
    }

    setNotice('Saved. Your clinic can see it in this pet’s file.');
    setBusy(false);
    formElement.reset();
    router.refresh();
  }

  return (
    <form className="stack" onSubmit={submit} style={{ marginTop: 12 }}>
      <div className="field">
        <label htmlFor="record_type">What is it?</label>
        <select id="record_type" name="record_type" defaultValue="VACCINE_CARD">
          {TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="record_file">Photo or PDF</label>
        <input
          id="record_file"
          name="file"
          type="file"
          required
          accept="application/pdf,image/jpeg,image/png,image/webp"
        />
      </div>
      <div className="field">
        <label htmlFor="record_note">Note (optional)</label>
        <input id="record_note" name="description" maxLength={500} placeholder="Rabies shot, 2019" />
      </div>

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
        {busy ? 'Uploading…' : 'Add to the file'}
      </button>
      <p className="fine">PDF, JPEG, PNG or WebP, up to 5 MB. Uploads stay unverified until a vet checks them.</p>
    </form>
  );
}
