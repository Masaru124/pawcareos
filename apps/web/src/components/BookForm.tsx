'use client';

import { useState } from 'react';

type Booking = {
  appointment_id: string;
  passport_slug: string;
  passport_url: string;
  clinic_name: string;
  doctor_name: string;
  reminders_queued: number;
  mode: string;
  room_url: string | null;
};

export function BookForm({
  doctorId,
  slot,
  mode = 'in_clinic',
}: {
  doctorId: string;
  slot: string;
  mode?: string;
}) {
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState<Booking | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    const response = await fetch('/api/bookings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doctor_id: doctorId,
        starts_at: slot,
        parent: {
          full_name: form.get('parent_name'),
          phone: form.get('phone'),
          email: form.get('email') || null,
        },
        patient: {
          name: form.get('pet_name'),
          species: form.get('species') || 'Canine',
          breed: form.get('breed') || null,
          gender: form.get('gender') || 'Unknown',
        },
        consent: form.get('consent') === 'on',
        mode,
      }),
    });

    const payload = (await response.json().catch(() => ({}))) as {
      error?: string;
      booking?: Booking;
    };

    if (!response.ok || !payload.booking) {
      setError(payload.error ?? `Booking failed (${response.status}).`);
      setBusy(false);
      return;
    }

    setBooking(payload.booking);
    setBusy(false);
  }

  if (booking) {
    return (
      <div className="stack">
        <p className="pill valid">Booked</p>
        <p>
          <strong>{booking.doctor_name}</strong> at {booking.clinic_name}.
        </p>
        <p className="muted">
          {booking.reminders_queued} reminder{booking.reminders_queued === 1 ? '' : 's'} queued.
          Their passport is already live.
        </p>
        <div className="row">
          <a className="button" href={`/p/${booking.passport_slug}`}>
            Open the passport
          </a>
          {booking.room_url && (
            <a className="button ghost" href={`/room/${booking.appointment_id}`}>
              Join the video room
            </a>
          )}
        </div>
      </div>
    );
  }

  return (
    <form className="stack" onSubmit={submit}>
      <div className="field">
        <label htmlFor="parent_name">Your name</label>
        <input id="parent_name" name="parent_name" required minLength={2} autoComplete="name" />
      </div>
      <div className="field">
        <label htmlFor="phone">WhatsApp number</label>
        <input
          id="phone"
          name="phone"
          required
          placeholder="+919876543210"
          pattern="^\+[1-9]\d{9,14}$"
          title="Include the country code, for example +919876543210"
        />
      </div>
      <div className="field">
        <label htmlFor="email">Email (optional)</label>
        <input id="email" name="email" type="email" autoComplete="email" />
      </div>
      <div className="field">
        <label htmlFor="pet_name">Pet’s name</label>
        <input id="pet_name" name="pet_name" required maxLength={100} />
      </div>
      <div className="field">
        <label htmlFor="species">Species</label>
        <select id="species" name="species" defaultValue="Canine">
          <option>Canine</option>
          <option>Feline</option>
          <option>Avian</option>
          <option>Exotic</option>
        </select>
      </div>
      <div className="field">
        <label htmlFor="breed">Breed (optional)</label>
        <input id="breed" name="breed" maxLength={100} />
      </div>
      <label style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <input type="checkbox" name="consent" defaultChecked />
        <span className="fine">
          Send appointment reminders on WhatsApp. Reply STOP any time.
        </span>
      </label>

      {error && (
        <p className="pill overdue" role="alert">
          {error}
        </p>
      )}

      <button className="button" type="submit" disabled={busy}>
        {busy ? 'Booking…' : 'Confirm booking'}
      </button>
    </form>
  );
}
