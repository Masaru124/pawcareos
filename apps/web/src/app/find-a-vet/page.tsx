import Link from 'next/link';

import { BookForm } from '@/components/BookForm';
import { ErrorPanel } from '@/components/ErrorPanel';
import { apiBase, apiDetail, publicFetch, readJson } from '@/lib/session';

type Doctor = {
  doctor_id: string;
  full_name: string;
  qualification: string | null;
  vci_suffix: string;
  clinic: { id: string; name: string; city: string; address: string; phone: string };
};

type Availability = {
  day: string;
  timezone: string;
  slots: { starts_at: string; label: string }[];
};

function today(): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata' }).format(new Date());
}

export default async function FindAVetPage({
  searchParams,
}: {
  searchParams: Promise<{
    q?: string;
    doctor?: string;
    date?: string;
    slot?: string;
    mode?: string;
  }>;
}) {
  const { q, doctor, date, slot, mode: modeParam } = await searchParams;
  const mode = modeParam === 'online' ? 'online' : 'in_clinic';
  const query = q?.trim() ?? '';
  const day = date ?? today();
  const listPath = query
    ? `/api/v1/directory/doctors?q=${encodeURIComponent(query)}`
    : '/api/v1/directory/doctors';

  let doctors: Doctor[] = [];
  let availability: Availability | null = null;
  let failure: { status?: number; detail: string } | null = null;

  try {
    const list = await publicFetch(listPath);
    if (list.ok) {
      doctors = (await list.json()) as Doctor[];
    } else {
      failure = { status: list.status, detail: apiDetail(await readJson(list), 'Vets did not load.') };
    }

    if (doctor) {
      const slots = await publicFetch(
        `/api/v1/directory/doctors/${doctor}/availability?date=${encodeURIComponent(day)}&mode=${mode}`,
      );
      if (slots.ok) availability = (await slots.json()) as Availability;
    }
  } catch (error) {
    failure = {
      detail: `${error instanceof Error ? error.message : 'No answer'} — the app calls ${apiBase()}.`,
    };
  }

  const chosen = doctors.find((item) => item.doctor_id === doctor);
  const chosenSlot = availability?.slots.find((item) => item.starts_at === slot);

  return (
    <main className="wrap" style={{ paddingTop: 48, maxWidth: 860 }}>
      <h1 style={{ fontSize: 'clamp(2rem, 5vw, 2.9rem)' }}>Book the next free slot.</h1>
      <p className="muted" style={{ marginTop: 10, maxWidth: 560 }}>
        Every doctor here holds a Veterinary Council of India registration on file. Pick a clinic
        slot, or an online consult at any hour — the passport, reminders and record are created in
        the same step.
      </p>

      <form action="/find-a-vet" method="get" className="search-form">
        <input
          name="q"
          defaultValue={query}
          placeholder="Vet, clinic or city"
          minLength={2}
          aria-label="Search vets"
        />
        <button className="button" type="submit">
          Search
        </button>
      </form>

      {failure && (
        <div style={{ marginTop: 22 }}>
          <ErrorPanel
            status={failure.status}
            title="The directory could not load"
            detail={failure.detail}
            hint="Start the API, or check PAWCARE_API_URL."
          />
        </div>
      )}

      {chosen && (
        <section className="card" style={{ padding: '26px 24px', marginTop: 26 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <p className="label">
                {mode === 'online' ? 'Online consult' : 'Clinic visit'} · chosen slot
              </p>
              <h2 style={{ fontSize: 22, marginTop: 6 }}>
                {chosen.full_name} · {chosen.clinic.name}
              </h2>
              <p className="fine" style={{ marginTop: 6 }}>
                {chosenSlot ? `${day} at ${chosenSlot.label}` : 'Pick a time below'}
              </p>
            </div>
            <Link className="button ghost" href={`/find-a-vet?${query ? `q=${encodeURIComponent(query)}&` : ''}`}>
              Start over
            </Link>
          </div>

          {chosenSlot ? (
            <div style={{ marginTop: 20 }}>
              <BookForm doctorId={chosen.doctor_id} slot={chosenSlot.starts_at} mode={mode} />
            </div>
          ) : (
            <div style={{ marginTop: 18 }}>
              {availability && availability.slots.length > 0 ? (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {availability.slots.map((item) => (
                    <Link
                      key={item.starts_at}
                      className="button ghost"
                      style={{ padding: '8px 14px' }}
                      href={`/find-a-vet?doctor=${chosen.doctor_id}&date=${day}&mode=${mode}&slot=${encodeURIComponent(item.starts_at)}${query ? `&q=${encodeURIComponent(query)}` : ''}`}
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="muted">
                  No free {mode === 'online' ? 'online slots' : 'slots'} on {day}. Try another day.
                </p>
              )}
              <form action="/find-a-vet" method="get" style={{ marginTop: 18, display: 'flex', gap: 10 }}>
                <input type="hidden" name="doctor" value={chosen.doctor_id} />
                <input type="hidden" name="mode" value={mode} />
                {query && <input type="hidden" name="q" value={query} />}
                <input type="date" name="date" defaultValue={day} aria-label="Choose a day" />
                <button className="button ghost" type="submit">
                  Show that day
                </button>
              </form>
            </div>
          )}
        </section>
      )}

      <section className="panel" style={{ marginTop: 30 }}>
        <div className="panel-head">
          <h2>
            {doctors.length} verified {doctors.length === 1 ? 'vet' : 'vets'}
          </h2>
          <span className="fine">{query ? `matching “${query}”` : 'across every clinic'}</span>
        </div>
        {doctors.length === 0 && !failure ? (
          <div className="empty">
            <h3>No vets match that search</h3>
            <p>Try a city, a clinic name, or the doctor’s own name.</p>
          </div>
        ) : (
          <ul className="doctor-list">
            {doctors.map((item) => {
              const initials = item.full_name
                .split(' ')
                .filter((part) => !part.endsWith('.'))
                .map((part) => part[0])
                .slice(0, 2)
                .join('');
              return (
                <li key={item.doctor_id} className="doctor-row">
                  <span className="doctor-mark" aria-hidden="true">
                    {initials}
                  </span>
                  <div className="doctor-main">
                    <strong>{item.full_name}</strong>
                    <span className="doctor-meta">
                      {item.qualification ?? 'B.V.Sc & A.H.'} · VCI {item.vci_suffix}
                    </span>
                    <span className="doctor-place">
                      {item.clinic.name} · {item.clinic.address}, {item.clinic.city}
                    </span>
                  </div>
                  <div className="doctor-actions">
                    <Link
                      className="button small"
                      href={`/find-a-vet?doctor=${item.doctor_id}&date=${day}${query ? `&q=${encodeURIComponent(query)}` : ''}`}
                    >
                      See slots
                    </Link>
                    <Link
                      className="button ghost small"
                      href={`/find-a-vet?doctor=${item.doctor_id}&date=${day}&mode=online${query ? `&q=${encodeURIComponent(query)}` : ''}`}
                    >
                      Online 24/7
                    </Link>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <p className="fine" style={{ marginTop: 26 }}>
        Already a client? <Link href="/login">Sign in</Link> to see your pet’s records.
      </p>
    </main>
  );
}
