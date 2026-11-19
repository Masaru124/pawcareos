import Link from 'next/link';
import { notFound } from 'next/navigation';

import { ErrorPanel } from '@/components/ErrorPanel';
import { apiBase, apiDetail, publicFetch, readJson } from '@/lib/session';

type Badge = { label: string; valid_until: string; state: string; doctor_name: string };
type Passport = {
  pet: {
    name: string;
    species: string;
    breed: string | null;
    age_label: string;
    sex_label: string;
    microchip_masked: string | null;
    passport_slug: string;
  };
  status: string;
  badges: Badge[];
  prescriptions: { date: string; doctor_name: string; rx_code: string }[];
  clinic: { name: string; address: string; phone: string };
};

const statusCopy: Record<string, string> = {
  fully_vaccinated: 'All boosters current',
  due_soon: 'A booster is due soon',
  overdue: 'A booster is overdue',
  no_records: 'No vaccines recorded yet',
};

function pretty(iso: string): string {
  const parsed = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return iso;
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(parsed);
}

export default async function PassportPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let response: Response;
  try {
    response = await publicFetch(`/p/${slug}`);
  } catch (error) {
    return (
      <main className="wrap" style={{ paddingTop: 56, maxWidth: 620 }}>
        <ErrorPanel
          title="The passport service is unreachable"
          detail={error instanceof Error ? error.message : 'The API did not answer.'}
          hint={`The web app calls ${apiBase()}. Start the API, or fix PAWCARE_API_URL.`}
        />
      </main>
    );
  }

  if (response.status === 404) notFound();

  if (!response.ok) {
    const detail = apiDetail(await readJson(response), 'The passport could not be loaded.');
    return (
      <main className="wrap" style={{ paddingTop: 56, maxWidth: 620 }}>
        <ErrorPanel status={response.status} title="The passport could not be loaded" detail={detail} />
      </main>
    );
  }

  const passport = (await response.json()) as Passport;
  const pet = passport.pet;

  return (
    <main className="wrap" style={{ paddingTop: 48, maxWidth: 720 }}>
      <p className="eyebrow">Pet passport · {passport.clinic.name}</p>
      <div className="card" style={{ padding: '32px 30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 18, flexWrap: 'wrap' }}>
          <div>
            <h1 style={{ fontSize: 'clamp(2rem, 5vw, 2.8rem)' }}>{pet.name}</h1>
            <p className="muted" style={{ marginTop: 6 }}>
              {pet.species}
              {pet.breed ? ` · ${pet.breed}` : ''} · {pet.sex_label} · {pet.age_label}
            </p>
          </div>
          <span className={`pill ${passport.status}`}>
            {statusCopy[passport.status] ?? passport.status}
          </span>
        </div>

        <div
          style={{
            marginTop: 28,
            paddingTop: 22,
            borderTop: '1px solid var(--line)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: 20,
          }}
        >
          <div>
            <p className="eyebrow" style={{ marginBottom: 6 }}>
              Passport
            </p>
            <p className="mono">{pet.passport_slug}</p>
          </div>
          <div>
            <p className="eyebrow" style={{ marginBottom: 6 }}>
              Microchip
            </p>
            <p className="mono">{pet.microchip_masked ?? 'Not recorded'}</p>
          </div>
        </div>

        <div style={{ marginTop: 30 }}>
          <p className="eyebrow">Vaccination record</p>
          {passport.badges.length === 0 ? (
            <p className="muted">
              No vaccines recorded yet. The clinic will add them at the next visit.
            </p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 12 }}>
              {passport.badges.map((badge) => (
                <li
                  key={badge.label}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: 16,
                    alignItems: 'baseline',
                    paddingBottom: 12,
                    borderBottom: '1px solid var(--line)',
                  }}
                >
                  <div>
                    <p style={{ fontWeight: 500 }}>{badge.label}</p>
                    <p className="fine">Valid until {pretty(badge.valid_until)}</p>
                  </div>
                  <span className={`pill ${badge.state}`}>
                    {badge.state === 'valid'
                      ? 'Current'
                      : badge.state === 'due_soon'
                        ? 'Due soon'
                        : 'Overdue'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {passport.prescriptions.length > 0 && (
          <div style={{ marginTop: 30 }}>
            <p className="eyebrow">Recent prescriptions</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 10 }}>
              {passport.prescriptions.map((item) => (
                <li
                  key={item.rx_code}
                  style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}
                >
                  <span className="mono">{item.rx_code}</span>
                  <span className="fine">
                    {pretty(item.date)} · {item.doctor_name}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div
          style={{
            marginTop: 32,
            paddingTop: 20,
            borderTop: '1px solid var(--line)',
            display: 'flex',
            justifyContent: 'space-between',
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <div className="fine">
            <p style={{ color: 'var(--ink-soft)' }}>{passport.clinic.name}</p>
            <p>{passport.clinic.address}</p>
            <p>{passport.clinic.phone}</p>
          </div>
          <a
            className="button ghost"
            href={`${apiBase()}/p/${pet.passport_slug}/certificate.pdf`}
            target="_blank"
            rel="noreferrer"
          >
            Vaccination certificate
          </a>
        </div>
      </div>
      <p className="fine" style={{ marginTop: 18 }}>
        Shared by your clinic. Anyone with this link can view the record — it never shows the full
        microchip number. <Link href="/">About PawCare OS</Link>
      </p>
    </main>
  );
}
