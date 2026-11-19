import Link from 'next/link';
import { redirect } from 'next/navigation';

import { ErrorPanel } from '@/components/ErrorPanel';
import { currentPrincipal } from '@/lib/principal';
import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

type PortalMe = {
  parent_name: string;
  phone_suffix: string;
  pets: {
    id: string;
    name: string;
    species: string;
    breed: string | null;
    passport_slug: string;
    clinic_name: string;
    next_due: string | null;
  }[];
};

type Appointment = {
  id: string;
  starts_at: string;
  patient_name: string;
  clinic_name: string;
  status: string;
  mode: string;
  room_url: string | null;
};

function pretty(iso: string): string {
  const parsed = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(parsed);
}

function prettyTime(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
}

export default async function PortalPage() {
  const principal = await currentPrincipal();
  if (!principal) redirect('/login');
  if (principal.kind !== 'parent') redirect(principal.home);

  const response = await authorisedFetch('/api/v1/portal/me');
  if (!response) redirect('/login');

  if (response.status === 401) {
    const detail = apiDetail(await readJson(response), 'This account is not linked to a pet yet.');
    return (
      <main className="wrap page" style={{ maxWidth: 640 }}>
        <ErrorPanel
          status={401}
          title="No pet records on this account"
          detail={detail}
          hint="Your clinic adds this email to your family record; the next sign-in claims it."
        />
        <div className="row" style={{ marginTop: 18 }}>
          <Link className="button ghost" href="/find-a-vet">
            Find a vet
          </Link>
          <Link className="button ghost" href="/logout">
            Sign out
          </Link>
        </div>
      </main>
    );
  }

  if (!response.ok) {
    const detail = apiDetail(await readJson(response), 'The portal could not load.');
    return (
      <main className="wrap page" style={{ maxWidth: 640 }}>
        <ErrorPanel status={response.status} title="The portal could not load" detail={detail} />
      </main>
    );
  }

  const me = (await response.json()) as PortalMe;
  const appointmentsResponse = await authorisedFetch('/api/v1/portal/appointments');
  const appointments =
    appointmentsResponse && appointmentsResponse.ok
      ? ((await appointmentsResponse.json()) as Appointment[])
      : [];
  const nextVisit = appointments[0];

  return (
    <main className="wrap page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Pet parent · passport</p>
          <h1>{me.parent_name}</h1>
          <div className="meta-line">
            <span>Number ending …{me.phone_suffix}</span>
            <span className="dot-sep" aria-hidden="true" />
            <span>
              {me.pets.length} {me.pets.length === 1 ? 'pet' : 'pets'} on this account
            </span>
          </div>
        </div>
        <div className="page-actions">
          <Link className="button" href="/find-a-vet">
            Book a visit
          </Link>
        </div>
      </header>

      <div className="board narrow">
        <section>
          <div className="panel">
            <div className="panel-head">
              <h2>Your pets</h2>
              <span className="fine">Records, passport, boosters</span>
            </div>

            {me.pets.length === 0 ? (
              <div className="empty">
                <h3>No pets yet</h3>
                <p>Your clinic adds your first pet at intake. The passport arrives with it.</p>
              </div>
            ) : (
              <ul className="day-list">
                {me.pets.map((pet) => (
                  <li key={pet.id} className="slot large">
                    <time>{pet.name.slice(0, 2).toUpperCase()}</time>
                    <div className="slot-main">
                      <strong>{pet.name}</strong>
                      <div className="slot-sub">
                        <span>
                          {pet.species}
                          {pet.breed ? ` · ${pet.breed}` : ''}
                        </span>
                        <span>· {pet.clinic_name}</span>
                      </div>
                      <div className="slot-sub">
                        {pet.next_due ? (
                          <span className="pill due_soon">Next due {pretty(pet.next_due)}</span>
                        ) : (
                          <span className="pill neutral">No boosters recorded</span>
                        )}
                      </div>
                    </div>
                    <div className="slot-side">
                      <Link className="button ghost tiny" href={`/p/${pet.passport_slug}`}>
                        Passport
                      </Link>
                      <Link className="button ghost tiny" href={`/portal/pets/${pet.id}`}>
                        Records
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <div className="side-stack">
          {nextVisit ? (
            <section className="focus-card">
              <p className="eyebrow">Next visit</p>
              <p className="focus-time">
                {prettyTime(nextVisit.starts_at)} ·{' '}
                {nextVisit.mode === 'online' ? 'video consult' : 'in clinic'}
              </p>
              <h2>{nextVisit.patient_name}</h2>
              <p className="focus-sub">{nextVisit.clinic_name}</p>
              <div className="focus-actions">
                {nextVisit.room_url && (
                  <Link className="button inverse small" href={`/room/${nextVisit.id}`}>
                    Join video
                  </Link>
                )}
                <Link className="button ghost inverse small" href="/find-a-vet">
                  Book another
                </Link>
              </div>
            </section>
          ) : (
            <section className="panel">
              <div className="panel-body">
                <p className="eyebrow">Next visit</p>
                <h2 style={{ fontSize: 22 }}>Nothing booked</h2>
                <p className="muted" style={{ marginTop: 8, fontSize: 14 }}>
                  When a booster is due, one WhatsApp message carries three times you can take.
                </p>
                <div className="row" style={{ marginTop: 14 }}>
                  <Link className="button small" href="/find-a-vet" style={{ flex: '1 1 auto' }}>
                    Find a slot
                  </Link>
                </div>
              </div>
            </section>
          )}

          <section className="panel">
            <div className="panel-head">
              <h3>Upcoming visits</h3>
              <span className="fine">{appointments.length}</span>
            </div>
            {appointments.length === 0 ? (
              <div className="panel-body">
                <p className="fine">Nothing booked yet.</p>
              </div>
            ) : (
              <ul className="list">
                {appointments.map((appointment) => (
                  <li key={appointment.id} className="list-row">
                    <div className="grow">
                      <strong>{appointment.patient_name}</strong>
                      <p className="fine">
                        {appointment.clinic_name} · {prettyTime(appointment.starts_at)}
                      </p>
                    </div>
                    <span className="pill neutral">{appointment.mode.replace('_', ' ')}</span>
                    {appointment.room_url && (
                      <Link className="button ghost tiny" href={`/room/${appointment.id}`}>
                        Join
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            )}
            <div className="panel-note">
              Reminders arrive on WhatsApp 24 hours and 2 hours before the visit.
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
