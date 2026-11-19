'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

type Medication = {
  name: string;
  dosage: string;
  frequency: string;
  duration_days: number;
};

type Result = {
  consultation_id: string;
  rx_code: string;
  passport_url: string;
  whatsapp_status: string;
};

const emptyMedication: Medication = {
  name: '',
  dosage: '',
  frequency: 'BD',
  duration_days: 5,
};

export function ConsultForm({ patientId, patientName }: { patientId: string; patientName: string }) {
  const idempotencyKey = useMemo(() => crypto.randomUUID(), []);
  const [medications, setMedications] = useState<Medication[]>([{ ...emptyMedication }]);
  const [giveVaccine, setGiveVaccine] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result | null>(null);

  function updateMedication(index: number, patch: Partial<Medication>) {
    setMedications((current) =>
      current.map((item, position) => (position === index ? { ...item, ...patch } : item)),
    );
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    const payload = {
      patient_id: patientId,
      weight_kg: form.get('weight_kg') ? Number(form.get('weight_kg')) : null,
      temperature_f: form.get('temperature_f') ? Number(form.get('temperature_f')) : null,
      symptoms: form.get('symptoms') || null,
      provisional_diagnosis: form.get('diagnosis'),
      medications: medications.filter((item) => item.name.trim().length > 0),
      vaccinations: giveVaccine
        ? [
            {
              kind: form.get('vaccine_kind'),
              vaccine_name: form.get('vaccine_name'),
              batch_number: form.get('batch_number'),
            },
          ]
        : [],
      dietary_advice: form.get('dietary_advice') || null,
      special_instructions: form.get('special_instructions') || null,
    };

    const response = await fetch('/api/consults', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify(payload),
    });

    const body = (await response.json().catch(() => ({}))) as Result & { detail?: unknown };
    if (!response.ok) {
      setError(readError(body));
      setBusy(false);
      return;
    }

    setResult(body);
    setBusy(false);
  }

  if (result) {
    return (
      <div className="card" style={{ marginTop: 26, padding: '30px 28px' }}>
        <p className="eyebrow">Issued</p>
        <h2 style={{ fontSize: 30 }}>{result.rx_code}</h2>
        <p className="muted" style={{ marginTop: 10 }}>
          The prescription for {patientName} is signed. WhatsApp delivery is{' '}
          <strong>{result.whatsapp_status === 'queued' ? 'queued (demo mode)' : 'suppressed — no consent on file'}</strong>.
        </p>
        <div className="row" style={{ marginTop: 22 }}>
          <Link className="button" href={result.passport_url}>
            Open the passport
          </Link>
          <Link className="button ghost" href="/enter">
            Back to my day
          </Link>
        </div>
        <p className="fine" style={{ marginTop: 16 }}>
          Submission {result.consultation_id.slice(0, 8)} · resubmitting with the same key would
          return this same prescription.
        </p>
      </div>
    );
  }

  return (
    <form className="stack" style={{ marginTop: 26 }} onSubmit={submit}>
      <div className="card stack" style={{ padding: '24px 22px' }}>
        <div className="row">
          <div className="field">
            <label htmlFor="weight_kg">Weight (kg)</label>
            <input id="weight_kg" name="weight_kg" type="number" step="0.1" min="0" max="200" />
          </div>
          <div className="field">
            <label htmlFor="temperature_f">Temperature (°F)</label>
            <input id="temperature_f" name="temperature_f" type="number" step="0.1" min="90" max="115" />
          </div>
        </div>
        <div className="field">
          <label htmlFor="symptoms">Symptoms</label>
          <textarea id="symptoms" name="symptoms" placeholder="Vomiting since last night, not eating" />
        </div>
        <div className="field">
          <label htmlFor="diagnosis">Provisional diagnosis</label>
          <input id="diagnosis" name="diagnosis" required minLength={3} placeholder="Acute gastroenteritis" />
        </div>
      </div>

      <div className="card stack" style={{ padding: '24px 22px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <p className="eyebrow" style={{ marginBottom: 0 }}>
            Prescription
          </p>
          <button
            className="button ghost"
            type="button"
            style={{ padding: '6px 12px' }}
            onClick={() => setMedications((current) => [...current, { ...emptyMedication }])}
          >
            Add drug
          </button>
        </div>

        {medications.map((medication, index) => (
          <div key={index} className="row" style={{ alignItems: 'flex-end' }}>
            <div className="field" style={{ flex: '2 1 200px' }}>
              <label>Drug {index + 1}</label>
              <input
                value={medication.name}
                onChange={(event) => updateMedication(index, { name: event.target.value })}
                placeholder="Metronidazole"
              />
            </div>
            <div className="field">
              <label>Strength</label>
              <input
                value={medication.dosage}
                onChange={(event) => updateMedication(index, { dosage: event.target.value })}
                placeholder="250 mg"
              />
            </div>
            <div className="field" style={{ flex: '0 1 110px' }}>
              <label>Frequency</label>
              <select
                value={medication.frequency}
                onChange={(event) => updateMedication(index, { frequency: event.target.value })}
              >
                {['OD', 'BD', 'TDS', 'QID', 'SOS'].map((option) => (
                  <option key={option}>{option}</option>
                ))}
              </select>
            </div>
            <div className="field" style={{ flex: '0 1 110px' }}>
              <label>Days</label>
              <input
                type="number"
                min={1}
                max={365}
                value={medication.duration_days}
                onChange={(event) =>
                  updateMedication(index, { duration_days: Number(event.target.value) })
                }
              />
            </div>
          </div>
        ))}
      </div>

      <div className="card stack" style={{ padding: '24px 22px' }}>
        <label style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: 15 }}>
          <input
            type="checkbox"
            checked={giveVaccine}
            onChange={(event) => setGiveVaccine(event.target.checked)}
          />
          A vaccine was given today
        </label>
        {giveVaccine && (
          <div className="row">
            <div className="field">
              <label htmlFor="vaccine_kind">Type</label>
              <select id="vaccine_kind" name="vaccine_kind">
                <option value="rabies">Rabies</option>
                <option value="dhppil">DHPPiL</option>
                <option value="deworming">Deworming</option>
                <option value="tricat">TriCat</option>
                <option value="kennel_cough">Kennel cough</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="vaccine_name">Vaccine name</label>
              <input id="vaccine_name" name="vaccine_name" defaultValue="Rabies" />
            </div>
            <div className="field">
              <label htmlFor="batch_number">Batch</label>
              <input id="batch_number" name="batch_number" required={giveVaccine} />
            </div>
          </div>
        )}
      </div>

      <div className="card stack" style={{ padding: '24px 22px' }}>
        <div className="field">
          <label htmlFor="dietary_advice">Dietary advice</label>
          <textarea id="dietary_advice" name="dietary_advice" placeholder="Boiled chicken and rice for three days" />
        </div>
        <div className="field">
          <label htmlFor="special_instructions">Special instructions</label>
          <textarea id="special_instructions" name="special_instructions" />
        </div>
      </div>

      {error && (
        <p className="pill overdue" role="alert">
          {error}
        </p>
      )}

      <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Issuing…' : 'Issue prescription'}
        </button>
        <span className="fine">One submission, one code. Retries reuse the same key.</span>
      </div>
    </form>
  );
}

function readError(body: { detail?: unknown }): string {
  const detail = body.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: string } | undefined;
    if (first?.msg) return first.msg.replace('Value error, ', '');
  }
  return 'The consult was refused. Check the diagnosis and at least one drug or vaccine.';
}
