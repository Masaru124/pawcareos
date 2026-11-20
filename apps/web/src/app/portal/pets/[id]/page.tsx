import Link from 'next/link';
import { redirect } from 'next/navigation';

import { ErrorPanel } from '@/components/ErrorPanel';
import { DeleteRecordButton } from '@/components/DeleteRecordButton';
import { LegacyRecordUpload } from '@/components/LegacyRecordUpload';
import { apiDetail, authorisedFetch, readJson } from '@/lib/session';

type Records = {
  pet_id: string;
  name: string;
  species: string;
  breed: string | null;
  passport_slug: string;
  clinic_name: string;
  vaccines: {
    vaccine_name: string;
    brand_name: string | null;
    batch_number: string;
    administered_date: string;
    next_due_date: string;
    status: string;
    doctor_name: string;
  }[];
  prescriptions: {
    rx_code: string;
    date: string;
    doctor_name: string;
    diagnosis: string;
    items: {
      medication_name: string;
      dosage_form: string;
      dosage_strength: string | null;
      frequency: string;
      duration_days: number;
      route: string;
      is_chronic: boolean;
    }[];
  }[];
  legacy_records: {
    id: string;
    record_type: string;
    description: string | null;
    file_name: string;
    content_type: string;
    size_bytes: number;
    uploaded_at: string;
  }[];
};

const RECORD_LABELS: Record<string, string> = {
  VACCINE_CARD: 'Vaccine card',
  EXTERNAL_RX: "Another clinic's prescription",
  LAB_REPORT: 'Lab report',
  XRAY: 'X-ray or scan',
  OTHER: 'Uploaded record',
};

function pretty(value: string): string {
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(parsed);
}

export default async function PetRecordsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const response = await authorisedFetch(`/api/v1/portal/pets/${id}/records`);
  if (!response) redirect('/login');

  if (!response.ok) {
    const detail = apiDetail(await readJson(response), 'These records could not be loaded.');
    return (
      <main className="wrap" style={{ paddingTop: 56, maxWidth: 620 }}>
        <ErrorPanel
          status={response.status}
          title="Records not available"
          detail={detail}
          hint="Records are readable only by the family the pet belongs to."
        />
        <p style={{ marginTop: 16 }}>
          <Link className="fine" href="/portal">
            Back to the portal
          </Link>
        </p>
      </main>
    );
  }

  const records = (await response.json()) as Records;

  return (
    <main className="wrap" style={{ paddingTop: 44, maxWidth: 820 }}>
      <p className="label">Digital health record · {records.clinic_name}</p>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: 'clamp(2rem, 5vw, 2.7rem)' }}>{records.name}</h1>
          <p className="muted" style={{ marginTop: 6 }}>
            {records.species}
            {records.breed ? ` · ${records.breed}` : ''} · passport {records.passport_slug}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <Link className="button ghost" href={`/p/${records.passport_slug}`}>
            Passport
          </Link>
          <Link className="button ghost" href="/portal">
            Portal
          </Link>
        </div>
      </div>

      <section style={{ marginTop: 30 }}>
        <p className="label">Vaccinations ({records.vaccines.length})</p>
        {records.vaccines.length === 0 ? (
          <p className="muted">No vaccines recorded yet.</p>
        ) : (
          <div className="card" style={{ marginTop: 12, overflow: 'hidden' }}>
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {records.vaccines.map((vaccine, index) => (
                <li
                  key={`${vaccine.vaccine_name}-${vaccine.administered_date}-${index}`}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: 14,
                    padding: '15px 22px',
                    borderTop: index === 0 ? 'none' : '1px solid var(--line)',
                    flexWrap: 'wrap',
                  }}
                >
                  <div style={{ flex: '1 1 220px' }}>
                    <p style={{ fontWeight: 500 }}>{vaccine.vaccine_name}</p>
                    <p className="fine">
                      {vaccine.brand_name ? `${vaccine.brand_name} · ` : ''}batch{' '}
                      {vaccine.batch_number} · {vaccine.doctor_name}
                    </p>
                  </div>
                  <span className="fine">Given {pretty(vaccine.administered_date)}</span>
                  <span className="mono">Next {pretty(vaccine.next_due_date)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section style={{ marginTop: 32 }}>
        <p className="label">Prescriptions ({records.prescriptions.length})</p>
        {records.prescriptions.length === 0 ? (
          <p className="muted">No prescriptions yet.</p>
        ) : (
          <div style={{ display: 'grid', gap: 14, marginTop: 12 }}>
            {records.prescriptions.map((prescription) => (
              <article key={prescription.rx_code} className="card" style={{ padding: '22px 22px' }}>
                <div
                  style={{ display: 'flex', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap' }}
                >
                  <div>
                    <p className="mono">{prescription.rx_code}</p>
                    <p style={{ marginTop: 6, fontWeight: 500 }}>{prescription.diagnosis}</p>
                    <p className="fine" style={{ marginTop: 4 }}>
                      {pretty(prescription.date)} · {prescription.doctor_name}
                    </p>
                  </div>
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: '14px 0 0', display: 'grid', gap: 8 }}>
                  {prescription.items.map((item) => (
                    <li key={item.medication_name} style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 500 }}>{item.medication_name}</span>
                      <span className="fine">
                        {[item.dosage_strength, item.dosage_form, item.frequency, `${item.duration_days} days`, item.route]
                          .filter(Boolean)
                          .join(' · ')}
                      </span>
                      {item.is_chronic && <span className="pill due_soon">chronic</span>}
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        )}
      </section>

      <section style={{ marginTop: 32 }}>
        <p className="label">From your files ({records.legacy_records.length})</p>
        <p className="fine" style={{ marginTop: 4 }}>
          Paper records you photographed yourself. {records.clinic_name} sees them in this pet’s file,
          but they stay unverified until a vet checks them.
        </p>

        {records.legacy_records.length > 0 && (
          <div className="card" style={{ marginTop: 12, overflow: 'hidden' }}>
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {records.legacy_records.map((record, index) => (
                <li
                  key={record.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: 14,
                    padding: '15px 22px',
                    borderTop: index === 0 ? 'none' : '1px solid var(--line)',
                    flexWrap: 'wrap',
                  }}
                >
                  <div style={{ flex: '1 1 220px' }}>
                    <p style={{ fontWeight: 500 }}>
                      <a
                        href={`/api/portal/pets/${records.pet_id}/records/${record.id}/file`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {RECORD_LABELS[record.record_type] ?? record.record_type}
                      </a>
                    </p>
                    <p className="fine">
                      {record.description ? `${record.description} · ` : ''}
                      {record.file_name} · {Math.max(1, Math.round(record.size_bytes / 1024))} KB
                    </p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className="pill due_soon">unverified</span>
                    <DeleteRecordButton petId={records.pet_id} recordId={record.id} />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="card" style={{ padding: '22px 22px', marginTop: 14 }}>
          <p className="label">Add a paper record</p>
          <LegacyRecordUpload petId={records.pet_id} />
        </div>
      </section>
    </main>
  );
}
