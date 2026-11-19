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

type FrontDesk = {
  date: string;
  timezone: string;
  clinic_name: string;
  opens_at: string;
  closes_at: string;
  counts: {
    total: number;
    waiting: number;
    checked_in: number;
    seen: number;
    online: number;
    cancelled: number;
  };
  arriving: Slot[];
  finished: Slot[];
};

const SOURCE_LABEL: Record<string, string> = {
  web: 'online booking',
  phone: 'phone',
  walk_in: 'walk-in',
  recall: 'recall',
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

export default async function FrontDeskPage() {
  const principal = await currentPrincipal();
  if (!principal) redirect('/login');
  if (
    principal.kind !== 'clinic' ||
    (principal.role !== 'receptionist' && principal.role !== 'owner')
  ) {
    redirect(principal.home);
  }

  const response = await authorisedFetch('/api/v1/dashboard/frontdesk');
  if (!response) redirect('/login');

  if (!response.ok) {
    const detail = apiDetail(await readJson(response), 'The desk board could not load.');
    return (
      <main className="wrap page" style={{ maxWidth: 640 }}>
        <ErrorPanel status={response.status} title="The desk board could not load" detail={detail} />
      </main>
    );
  }

  const desk = (await response.json()) as FrontDesk;

  return (
    <main className="wrap page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Front desk · arrivals</p>
          <h1>{desk.clinic_name}</h1>
          <div className="meta-line">
            <span>{longDate(desk.date)}</span>
            <span className="dot-sep" aria-hidden="true" />
            <span>
              Open {desk.opens_at}–{desk.closes_at}
            </span>
            <span className="dot-sep" aria-hidden="true" />
            <span>{desk.counts.online} online today</span>
          </div>
        </div>
        <div className="page-actions">
          <Link className="button" href="/find-a-vet">
            Book a visit
          </Link>
          <Link className="button ghost" href="/patients">
            Patients
          </Link>
        </div>
      </header>

      <section className="stat-strip" aria-label="The desk right now">
        <div className="stat">
          <div className="stat-value">{desk.counts.total}</div>
          <div className="stat-label">On the list</div>
        </div>
        <div className="stat">
          <div className="stat-value">{desk.counts.waiting}</div>
          <div className="stat-label">Not arrived</div>
        </div>
        <div className="stat is-alert">
          <div className="stat-value">{desk.counts.checked_in}</div>
          <div className="stat-label">In the waiting room</div>
        </div>
        <div className="stat">
          <div className="stat-value">{desk.counts.seen}</div>
          <div className="stat-label">Seen</div>
        </div>
        <div className="stat">
          <div className="stat-value">{desk.counts.cancelled}</div>
          <div className="stat-label">Cancelled</div>
        </div>
      </section>

      <div className="board">
        <section className="panel">
          <div className="panel-head">
            <h2>Arriving</h2>
            <span className="fine">{desk.arriving.length} still to come</span>
          </div>

          {desk.arriving.length === 0 ? (
            <div className="empty">
              <h3>Everyone is through</h3>
              <p>
                No one is waiting to be checked in. New online bookings land here automatically.
              </p>
              <div className="empty-actions">
                <Link className="button small" href="/find-a-vet">
                  Open the booking page
                </Link>
              </div>
            </div>
          ) : (
            <ul className="day-list">
              {desk.arriving.map((slot) => (
                <li key={slot.id} className="slot large">
                  <time>{slot.starts_at}</time>
                  <div className="slot-main">
                    <strong>{slot.patient_name}</strong>
                    <div className="slot-sub">
                      <span>
                        {slot.species}
                        {slot.breed ? ` · ${slot.breed}` : ''}
                      </span>
                      {slot.parent_name && (
                        <span>
                          · {slot.parent_name}
                          {slot.parent_phone_suffix ? ` · …${slot.parent_phone_suffix}` : ''}
                        </span>
                      )}
                    </div>
                    <div className="slot-sub">
                      <span>{slot.doctor_name ?? 'Any available vet'}</span>
                      <span>· {SOURCE_LABEL[slot.source] ?? slot.source}</span>
                      {slot.mode === 'online' && <span>· video</span>}
                    </div>
                    {slot.allergies.length > 0 && (
                      <p className="note rose">Allergy: {slot.allergies.join(', ')}</p>
                    )}
                  </div>
                  <div className="slot-side">
                    <span className={`pill ${slot.status === 'confirmed' ? 'valid' : 'neutral'}`}>
                      {slot.status === 'confirmed' ? 'in clinic' : 'expected'}
                    </span>
                    <AppointmentActions id={slot.id} status={slot.status} desk />
                  </div>
                </li>
              ))}
            </ul>
          )}

          {desk.finished.length > 0 && (
            <>
              <div className="panel-head" style={{ borderTop: '1px solid var(--line)' }}>
                <h3>Seen today</h3>
                <span className="fine">{desk.finished.length}</span>
              </div>
              <ul className="day-list">
                {desk.finished.map((slot) => (
                  <li key={slot.id} className="slot is-done">
                    <time>{slot.starts_at}</time>
                    <div className="slot-main">
                      <strong>{slot.patient_name}</strong>
                      <div className="slot-sub">
                        <span>{slot.parent_name ?? slot.species}</span>
                        {slot.doctor_name && <span>· {slot.doctor_name}</span>}
                      </div>
                    </div>
                    <div className="slot-side">
                      <span className="pill neutral">seen</span>
                      <Link className="button ghost tiny" href={`/p/${slot.passport_slug}`}>
                        Passport
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>

        <div className="side-stack">
          <section className="panel">
            <div className="panel-head">
              <h3>At the desk</h3>
            </div>
            <div className="panel-body stack" style={{ gap: 12 }}>
              <p className="muted" style={{ fontSize: 14 }}>
                Check in with one tap. If someone has not booked, open the booking page on the
                parent’s phone — the passport is issued with the visit.
              </p>
              <div className="row" style={{ gap: 8 }}>
                <Link className="button small" href="/find-a-vet" style={{ flex: '1 1 auto' }}>
                  Book / walk in
                </Link>
                <Link className="button ghost small" href="/patients" style={{ flex: '1 1 auto' }}>
                  Find a patient
                </Link>
              </div>
            </div>
            <div className="panel-note">
              Reminders go out on WhatsApp 24 hours and 2 hours before the slot, in demo mode.
            </div>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h3>The rest of the day</h3>
            </div>
            <ul className="list">
              <li className="list-row">
                <span className="grow">Still expected</span>
                <span className="mono">{desk.counts.waiting}</span>
              </li>
              <li className="list-row">
                <span className="grow">Waiting to be seen</span>
                <span className="mono">{desk.counts.checked_in}</span>
              </li>
              <li className="list-row">
                <span className="grow">Online consults</span>
                <span className="mono">{desk.counts.online}</span>
              </li>
              <li className="list-row">
                <span className="grow">Off the board</span>
                <span className="mono">{desk.counts.cancelled}</span>
              </li>
            </ul>
            {principal.role === 'owner' && (
              <div className="panel-note">
                <Link href="/admin">Open the owner panel</Link> for the week and the team.
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
