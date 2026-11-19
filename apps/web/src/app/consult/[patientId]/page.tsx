import Link from 'next/link';
import { notFound, redirect } from 'next/navigation';

import { ConsultForm } from '@/components/ConsultForm';
import { ErrorPanel } from '@/components/ErrorPanel';
import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

type Patient = {
  id: string;
  name: string;
  species: string;
  breed: string | null;
  passport_slug: string;
};

export default async function ConsultPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = await params;
  const response = await authorisedFetch(`/api/v1/patients/${patientId}`);
  if (!response) redirect('/login');
  if (response.status === 404) notFound();

  if (!response.ok) {
    return (
      <main className="wrap" style={{ paddingTop: 56, maxWidth: 620 }}>
        <ErrorPanel
          status={response.status}
          title="This patient could not be loaded"
          detail={apiDetail(await readJson(response), 'The API refused the request.')}
          hint="Ask reception to confirm the patient belongs to this clinic."
        />
      </main>
    );
  }

  const patient = (await response.json()) as Patient;

  return (
    <main className="wrap" style={{ paddingTop: 44, paddingBottom: 40, maxWidth: 860 }}>
      <Link className="fine" href="/enter">
        ← Back to my day
      </Link>
      <p className="eyebrow" style={{ marginTop: 18 }}>
        Consult · {patient.species}
        {patient.breed ? ` · ${patient.breed}` : ''}
      </p>
      <h1 style={{ fontSize: 'clamp(1.9rem, 4vw, 2.6rem)' }}>{patient.name}</h1>
      <p className="fine" style={{ marginTop: 6 }}>
        Passport <span className="mono">{patient.passport_slug}</span>
      </p>
      <ConsultForm patientId={patient.id} patientName={patient.name} />
    </main>
  );
}
