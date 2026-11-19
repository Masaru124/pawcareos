import Link from 'next/link';
import { redirect } from 'next/navigation';

import { AppointmentActions } from '@/components/AppointmentActions';
import { ErrorPanel } from '@/components/ErrorPanel';
import { StaffInviteForm } from '@/components/StaffInviteForm';
import { currentPrincipal } from '@/lib/principal';
import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

type Overview = {
  clinic: {
    name: string;
    city: string;
    address: string;
    phone: string;
    timezone: string;
    opens_at: string;
    closes_at: string;
  };
  counts: {
    patients: number;
    appointments_today: number;
    online_today: number;
    upcoming_week: number;
    overdue_vaccines: number;
    doctors: number;
    staff: number;
  };
  staff: {
    id: string;
    full_name: string;
    email: string;
    role: string;
    claimed: boolean;
    is_active: boolean;
    vci_suffix: string | null;
  }[];
  activity: {
    action: string;
    subject_type: string;
    created_at: string;
    actor_name: string | null;
  }[];
};

type Slot = {
  id: string;
  starts_at: string;
  patient_name: string;
  species: string;
  parent_name: string | null;
  status: string;
  source: string;
  mode: string;
  doctor_name: string | null;
};

type FrontDesk = {
  date: string;
  counts: { total: number; waiting: number; checked_in: number; seen: number };
  arriving: Slot[];
  finished: Slot[];
};

const ROLE_PILL: Record<string, string> = {
  owner: 'valid',
  doctor: 'neutral',
  receptionist: 'neutral',
};

const PILL: Record<string, { className: string; label: string }> = {
  booked: { className: 'neutral', label: 'due' },
  confirmed: { className: 'valid', label: 'in clinic' },
  completed: { className: 'neutral', label: 'seen' },
  cancelled: { className: 'overdue', label: 'cancelled' },
};

function when(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
}

function longDate(value: string): string {
  const parsed = new Date(`${value}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(parsed);
}

export default async function AdminPage() {
  const principal = await currentPrincipal();
  if (!principal) redirect('/login');
  if (principal.kind !== 'clinic' || principal.role !== 'owner') redirect(principal.home);

  const [overviewResponse, deskResponse] = await Promise.all([
    authorisedFetch('/api/v1/admin/overview'),
    authorisedFetch('/api/v1/dashboard/frontdesk'),
  ]);
  if (!overviewResponse) redirect('/login');

  if (!overviewResponse.ok) {
    const detail = apiDetail(await readJson(overviewResponse), 'The panel could not load.');
    return (
      <main className="wrap page" style={{ maxWidth: 640 }}>
        <ErrorPanel status={overviewResponse.status} title="The owner panel could not load" detail={detail} />
      </main>
    );
  }

  const overview = (await overviewResponse.json()) as Overview;
  const desk =
    deskResponse && deskResponse.ok ? ((await deskResponse.json()) as FrontDesk) : null;
  const { counts, clinic } = overview;

  const today = desk
    ? [...desk.arriving, ...desk.finished].sort((a, b) => a.starts_at.localeCompare(b.starts_at))
    : [];

  return (
    <main className="wrap page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Owner · operations</p>
          <h1>{clinic.name}</h1>
          <div className="meta-line">
            <span>
              {clinic.address}, {clinic.city}
            </span>
            <span className="dot-sep" aria-hidden="true" />
            <span>
              {clinic.opens_at}–{clinic.closes_at} · {clinic.timezone.replace('_', ' ')}
            </span>
            <span className="dot-sep" aria-hidden="true" />
            <span>{clinic.phone}</span>
          </div>
        </div>
        <div className="page-actions">
          <Link className="button ghost" href="/frontdesk">
            Front desk
          </Link>
          <Link className="button ghost" href="/patients">
            Patients
          </Link>
        </div>
      </header>

      <section className="stat-strip" aria-label="Clinic at a glance">
        <div className="stat">
          <div className="stat-value">{counts.patients}</div>
          <div className="stat-label">Active patients</div>
        </div>
        <div className="stat">
          <div className="stat-value">{counts.appointments_today}</div>
          <div className="stat-label">Appointments today</div>
          {counts.online_today > 0 && (
            <div className="stat-note">{counts.online_today} online</div>
          )}
        </div>
        <div className="stat">
          <div className="stat-value">{counts.upcoming_week}</div>
          <div className="stat-label">Next 7 days</div>
        </div>
        <div className={`stat${counts.overdue_vaccines > 0 ? ' is-alert' : ''}`}>
          <div className="stat-value">{counts.overdue_vaccines}</div>
          <div className="stat-label">Overdue boosters</div>
        </div>
        <div className="stat">
          <div className="stat-value">{counts.doctors}</div>
          <div className="stat-label">Doctors</div>
        </div>
        <div className="stat">
          <div className="stat-value">{counts.staff}</div>
          <div className="stat-label">Staff</div>
        </div>
      </section>

      <div className="board">
        <section className="panel">
          <div className="panel-head">
            <h2>Today</h2>
            <span className="fine">{desk ? longDate(desk.date) : 'Clinic board'}</span>
          </div>

          {!desk ? (
            <div className="panel-body">
              <p className="fine">The day board is temporarily unavailable.</p>
            </div>
          ) : today.length === 0 ? (
            <div className="empty">
              <h3>A clear day</h3>
              <p>Nothing is booked. The front desk can add a walk-in or send the booking link.</p>
              <div className="empty-actions">
                <Link className="button small" href="/find-a-vet">
                  Booking page
                </Link>
              </div>
            </div>
          ) : (
            <ul className="day-list">
              {today.map((slot) => {
                const pill = PILL[slot.status] ?? PILL.booked;
                const live = slot.status === 'booked' || slot.status === 'confirmed';
                return (
                  <li
                    key={slot.id}
                    className={[
                      'slot',
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
                        <span>{slot.species}</span>
                        {slot.parent_name && <span>· {slot.parent_name}</span>}
                        {slot.doctor_name && <span>· {slot.doctor_name}</span>}
                        {slot.mode === 'online' && <span>· video</span>}
                      </div>
                    </div>
                    <div className="slot-side">
                      <span className={`pill ${pill.className}`}>{pill.label}</span>
                      {live && <AppointmentActions id={slot.id} status={slot.status} desk />}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}

          {desk && (
            <div className="panel-note">
              {desk.counts.waiting} expected · {desk.counts.checked_in} in the waiting room ·{' '}
              {desk.counts.seen} seen. <Link href="/frontdesk">Open the desk board</Link>
            </div>
          )}
        </section>

        <div className="side-stack">
          <section className="panel">
            <div className="panel-head">
              <h3>Team</h3>
              <span className="fine">{overview.staff.length}</span>
            </div>
            <ul className="list">
              {overview.staff.map((member) => (
                <li key={member.id} className="list-row">
                  <div className="grow">
                    <strong>{member.full_name}</strong>
                    <p className="fine">
                      {member.email}
                      {member.vci_suffix ? ` · VCI ${member.vci_suffix}` : ''}
                    </p>
                  </div>
                  <span className={`pill ${ROLE_PILL[member.role] ?? 'neutral'}`}>
                    {member.role}
                  </span>
                  <span className={`pill ${member.claimed ? 'valid' : 'due_soon'}`}>
                    {member.claimed ? 'signed in' : 'invited'}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h3>Invite a colleague</h3>
            </div>
            <div className="panel-body">
              <StaffInviteForm />
            </div>
            <div className="panel-note">
              An invited address claims its clinic profile the first time it signs in.
            </div>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h3>Recent activity</h3>
            </div>
            {overview.activity.length === 0 ? (
              <div className="panel-body">
                <p className="fine">Nothing recorded yet.</p>
              </div>
            ) : (
              <ul className="list">
                {overview.activity.map((entry, index) => (
                  <li key={`${entry.action}-${entry.created_at}-${index}`} className="list-row">
                    <div className="grow">
                      <strong className="mono" style={{ fontSize: 12.5 }}>
                        {entry.action}
                      </strong>
                      <p className="fine">
                        {entry.actor_name ?? 'system'} · {when(entry.created_at)}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
