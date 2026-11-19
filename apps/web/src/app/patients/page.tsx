import Link from 'next/link';
import { redirect } from 'next/navigation';

import { ErrorPanel } from '@/components/ErrorPanel';
import { currentPrincipal } from '@/lib/principal';
import { apiDetail, authorisedFetch, readJson, sessionEmail } from '@/lib/session';

type Patient = {
  id: string;
  name: string;
  species: string;
  breed: string | null;
  passport_slug: string;
  parent_name: string | null;
  parent_phone_suffix: string | null;
};

export default async function PatientsPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  const principal = await currentPrincipal();
  const canConsult =
    principal?.kind === 'clinic' &&
    (principal.role === 'doctor' || principal.role === 'owner');
  const query = q?.trim() ?? '';
  const path = query ? `/api/v1/patients?q=${encodeURIComponent(query)}` : '/api/v1/patients';

  const response = await authorisedFetch(path);
  if (!response) redirect('/login');

  if (response.status === 401) {
    const email = await sessionEmail();
    return (
      <main className="wrap" style={{ paddingTop: 56, maxWidth: 620 }}>
        <ErrorPanel
          status={401}
          title="This account is not linked to a clinic yet"
          detail={`You are signed in${email ? ` as ${email}` : ''}, but PawCare has no clinic user for that address.`}
          hint="An owner adds the address to clinic_users; the next request claims it automatically."
        />
      </main>
    );
  }

  if (!response.ok) {
    const detail = apiDetail(await readJson(response), 'The directory did not load.');
    return (
      <main className="wrap" style={{ paddingTop: 56, maxWidth: 620 }}>
        <ErrorPanel
          status={response.status}
          title="Patients could not load"
          detail={detail}
          hint="A search needs at least two characters."
        />
      </main>
    );
  }

  const patients = ((await response.json()) as { items: Patient[] }).items;

  return (
    <main className="wrap" style={{ paddingTop: 48 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <p className="eyebrow">Patient directory</p>
          <h1 style={{ fontSize: 'clamp(2rem, 4vw, 2.7rem)' }}>Every passport.</h1>
          <p className="muted" style={{ marginTop: 10, maxWidth: 520 }}>
            Search by pet name, the last four digits of the owner’s phone, or a microchip number.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <Link className="button ghost" href={principal?.home ?? '/login'}>
            {principal?.label ?? 'Sign in'}
          </Link>
          <a className="button ghost" href="/logout">
            Sign out
          </a>
        </div>
      </div>

      <form action="/patients" method="get" className="search-form">
        <input
          name="q"
          defaultValue={query}
          placeholder="Bruno, 4321, 98102…"
          minLength={2}
          aria-label="Search patients"
        />
        <button className="button" type="submit">
          Search
        </button>
      </form>
      {query && (
        <p className="fine" style={{ marginTop: 8 }}>
          {patients.length} match{patients.length === 1 ? '' : 'es'} for “{query}”.{' '}
          <Link href="/patients">Clear</Link>
        </p>
      )}

      <div className="card" style={{ marginTop: 18, overflow: 'hidden' }}>
        {patients.length === 0 ? (
          <div style={{ padding: '30px 26px' }}>
            <p style={{ fontWeight: 500 }}>
              {query ? 'No pet matches that.' : 'No patients yet.'}
            </p>
            <p className="muted" style={{ marginTop: 8 }}>
              {query
                ? 'Try the owner’s last four phone digits, or a shorter name.'
                : 'Reception adds the first patient at intake; the passport is issued with it.'}
            </p>
          </div>
        ) : (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {patients.map((patient, index) => (
              <li
                key={patient.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  padding: '16px 22px',
                  borderTop: index === 0 ? 'none' : '1px solid var(--line)',
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ flex: '1 1 200px' }}>
                  <p style={{ fontWeight: 500 }}>{patient.name}</p>
                  <p className="fine">
                    {patient.species}
                    {patient.breed ? ` · ${patient.breed}` : ''}
                    {patient.parent_name ? ` · ${patient.parent_name}` : ''}
                    {patient.parent_phone_suffix ? ` · …${patient.parent_phone_suffix}` : ''}
                  </p>
                </div>
                <span className="mono" style={{ color: 'var(--ink-faint)' }}>
                  {patient.passport_slug}
                </span>
                <Link
                  className="button ghost"
                  href={`/p/${patient.passport_slug}`}
                  style={{ padding: '7px 14px' }}
                >
                  Passport
                </Link>
                {canConsult && (
                  <Link
                    className="button"
                    href={`/consult/${patient.id}`}
                    style={{ padding: '7px 14px' }}
                  >
                    Consult
                  </Link>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
