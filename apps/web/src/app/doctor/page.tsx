import Link from 'next/link';
import { redirect } from 'next/navigation';

import { AppointmentActions } from '@/components/AppointmentActions';
import { ErrorPanel } from '@/components/ErrorPanel';
import { currentPrincipal } from '@/lib/principal';
import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

type Slot = {
  id: string;
  starts_at: string;
  patient_id: string;
  patient_name: string;
  species: string;
  breed: string | null;
  passport_slug: string;
  parent_name: string | null;
  parent_phone_suffix: string | null;
  status: string;
  source: string;
  mode: string;
  room_url: string | null;
  doctor_name: string | null;
  allergies: string[];
  chronic_conditions: string[];
};

type DoctorDay = {
  date: string;
  timezone: string;
  doctor_name: string;
  counts: {
    total: number;
    waiting: number;
    checked_in: number;
    seen: number;
    online: number;
    cancelled: number;
  };
  appointments: Slot[];
  next_up: Slot | null;
};

const PILL: Record<string, { className: string; label: string }> = {
  booked: { className: 'neutral', label: 'due' },
  confirmed: { className: 'valid', label: 'arrived' },
  completed: { className: 'neutral', label: 'seen' },
  cancelled: { className: 'overdue', label: 'cancelled' },
};

function longDate(value: string): string {
  const parsed = new Date(`${value}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(parsed);
}

export default async function DoctorPage() {
  const principal = await currentPrincipal();
  if (!principal) redirect('/login');
  if (principal.kind !== 'clinic' || principal.role !== 'doctor') redirect(principal.home);

  const response = await authorisedFetch('/api/v1/dashboard/doctor');
  if (!response) redirect('/login');

  if (!response.ok) {
    const detail = apiDetail(await readJson(response), 'Your day could not load.');
    return (
      <main className="wrap page" style={{ maxWidth: 640 }}>
        <ErrorPanel
          status={response.status}
          title="Your day could not load"
          detail={detail}
          hint="Doctors sign in with a VCI registration number on their clinic profile."
        />
      </main>
    );
  }

  const day = (await response.json()) as DoctorDay;
  const given = principal.name.replace(/^dr\.?\s+/i, '').split(' ')[0];
  const next = day.next_up;
  const watch = day.appointments.filter(
    (slot) =>
      slot.allergies.length > 0 ||
      slot.chronic_conditions.length > 0,
  );

  return (
    <main className="wrap page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Doctor · clinical day</p>
          <h1>Your day, {given}.</h1>
          <div className="meta-line">
            <span>{longDate(day.date)}</span>
            <span className="dot-sep" aria-hidden="true" />
            <span>{day.timezone.replace('_', ' ')}</span>
            <span className="dot-sep" aria-hidden="true" />
            <span>
              {day.counts.total} booked · {day.counts.seen} seen
            </span>
          </div>
        </div>
        <div className="page-actions">
          <Link className="button ghost" href="/patients">
            Patient directory
          </Link>
        </div>
      </header>

      <section className="stat-strip" aria-label="Today at a glance">
        <div className="stat">
          <div className="stat-value">{day.counts.total}</div>
          <div className="stat-label">Booked</div>
        </div>
        <div className="stat">
          <div className="stat-value">{day.counts.waiting}</div>
          <div className="stat-label">Still to arrive</div>
        </div>
        <div className="stat">
          <div className="stat-value">{day.counts.checked_in}</div>
          <div className="stat-label">Checked in</div>
        </div>
        <div className="stat">
          <div className="stat-value">{day.counts.seen}</div>
          <div className="stat-label">Seen</div>
        </div>
        <div className="stat">
          <div className="stat-value">{day.counts.online}</div>
          <div className="stat-label">Online</div>
        </div>
      </section>

      <div className="board">
        <section className="panel">
          <div className="panel-head">
            <h2>Schedule</h2>
            <span className="fine">{day.appointments.length} appointments</span>
          </div>

          {day.appointments.length === 0 ? (
            <div className="empty">
              <h3>Nothing booked with you today</h3>
              <p>
                Appointments appear here once a parent books your slot or the front desk puts them
                on your list.
              </p>
              <div className="empty-actions">
                <Link className="button ghost small" href="/patients">
                  Open the patient directory
                </Link>
              </div>
            </div>
          ) : (
            <ul className="day-list">
              {day.appointments.map((slot) => {
                const pill = PILL[slot.status] ?? PILL.booked;
                const isNext = next?.id === slot.id;
                const live = slot.status !== 'completed' && slot.status !== 'cancelled';
                return (
                  <li
                    key={slot.id}
                    className={[
                      'slot',
                      isNext ? 'is-next' : '',
                      slot.status === 'completed' ? 'is-done' : '',
                      slot.status === 'cancelled' ? 'is-out' : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                  >
                    <time>{slot.starts_at}</time>
                    <div className="slot-main">
                      <strong>{slot.patient_name}</strong>
                      <div className="slot-sub">
                        <span>
                          {slot.species}
                          {slot.breed ? ` · ${slot.breed}` : ''}
                        </span>
                        {slot.parent_name && <span>· {slot.parent_name}</span>}
                        {slot.mode === 'online' && <span>· video</span>}
                      </div>
                      {slot.allergies.length > 0 && (
                        <p className="note rose">Allergy: {slot.allergies.join(', ')}</p>
                      )}
                      {slot.chronic_conditions.length > 0 && (
                        <p className="note">Chronic: {slot.chronic_conditions.join(', ')}</p>
                      )}
                    </div>
                    <div className="slot-side">
                      <span className={`pill ${pill.className}`}>{pill.label}</span>
                      {live && (
                        <>
                          <Link className="button ghost tiny" href={`/consult/${slot.patient_id}`}>
                            Consult
                          </Link>
                          {slot.room_url && (
                            <Link className="button tiny" href={`/room/${slot.id}`}>
                              Video
                            </Link>
                          )}
                        </>
                      )}
                      {(slot.status === 'booked' || slot.status === 'confirmed') && (
                        <AppointmentActions id={slot.id} status={slot.status} />
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <div className="side-stack">
          {next ? (
            <section className="focus-card" aria-label="Next appointment">
              <p className="eyebrow">Next up</p>
              <p className="focus-time">
                {next.starts_at} · {next.mode === 'online' ? 'video consult' : 'in clinic'}
              </p>
              <h2>{next.patient_name}</h2>
              <p className="focus-sub">
                {next.species}
                {next.breed ? ` · ${next.breed}` : ''}
                {next.parent_name ? ` · ${next.parent_name}` : ''}
              </p>
              {(next.allergies.length > 0 || next.chronic_conditions.length > 0) && (
                <p className="focus-note">
                  {next.allergies.length > 0 && <>Allergies: {next.allergies.join(', ')}. </>}
                  {next.chronic_conditions.length > 0 && (
                    <>Chronic: {next.chronic_conditions.join(', ')}.</>
                  )}
                </p>
              )}
              <div className="focus-actions">
                <Link className="button inverse small" href={`/consult/${next.patient_id}`}>
                  Open consult
                </Link>
                {next.room_url && (
                  <Link className="button ghost inverse small" href={`/room/${next.id}`}>
                    Join video
                  </Link>
                )}
                <Link className="button ghost inverse small" href={`/p/${next.passport_slug}`}>
                  Passport
                </Link>
              </div>
            </section>
          ) : (
            <section className="panel focus-empty">
              <div className="panel-body">
                <p className="eyebrow">Next up</p>
                <h2>Day is clear</h2>
                <p className="muted" style={{ marginTop: 8, fontSize: 14 }}>
                  Nothing is waiting. Your next booking will appear here with the pet’s notes.
                </p>
              </div>
            </section>
          )}

          <section className="panel">
            <div className="panel-head">
              <h3>Watch for</h3>
              <span className="fine">{watch.length}</span>
            </div>
            {watch.length === 0 ? (
              <div className="panel-body">
                <p className="fine">No allergies or chronic notes on today’s patients.</p>
              </div>
            ) : (
              <ul className="list">
                {watch.map((slot) => (
                  <li key={`watch-${slot.id}`} className="list-row">
                    <div className="grow">
                      <strong>{slot.patient_name}</strong>
                      <p className="fine">
                        {[...slot.allergies, ...slot.chronic_conditions].join(' · ')}
                      </p>
                    </div>
                    <span className="mono">{slot.starts_at}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="panel">
            <div className="panel-body">
              <p className="eyebrow" style={{ marginBottom: 8 }}>
                Quick jump
              </p>
              <div className="row" style={{ gap: 8 }}>
                <Link className="button ghost small" href="/patients" style={{ flex: '1 1 auto' }}>
                  Search patients
                </Link>
                <Link className="button ghost small" href="/find-a-vet" style={{ flex: '1 1 auto' }}>
                  Booking page
                </Link>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
