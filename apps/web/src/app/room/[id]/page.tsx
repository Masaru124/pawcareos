import Link from 'next/link';
import { notFound } from 'next/navigation';

import { ErrorPanel } from '@/components/ErrorPanel';
import { apiBase, apiDetail, publicFetch, readJson } from '@/lib/session';

type Room = {
  appointment_id: string;
  starts_at: string;
  mode: string;
  room_url: string | null;
  clinic_name: string;
  doctor_name: string;
  patient_name: string;
};

export default async function RoomPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let response: Response;
  try {
    response = await publicFetch(`/api/v1/directory/rooms/${id}`);
  } catch (error) {
    return (
      <main className="wrap" style={{ paddingTop: 56, maxWidth: 620 }}>
        <ErrorPanel
          title="The consult room is unreachable"
          detail={error instanceof Error ? error.message : 'The API did not answer.'}
          hint={`The app calls ${apiBase()}.`}
        />
      </main>
    );
  }

  if (response.status === 404) notFound();

  if (!response.ok) {
    return (
      <main className="wrap" style={{ paddingTop: 56, maxWidth: 620 }}>
        <ErrorPanel
          status={response.status}
          title="This consult room could not be opened"
          detail={apiDetail(await readJson(response), 'The room is not available.')}
        />
      </main>
    );
  }

  const room = (await response.json()) as Room;
  const when = new Intl.DateTimeFormat('en-IN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(room.starts_at));

  return (
    <main className="wrap" style={{ paddingTop: 36, maxWidth: 900 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <p className="eyebrow">Online consult · {room.clinic_name}</p>
          <h1 style={{ fontSize: 30 }}>{room.patient_name}</h1>
          <p className="fine" style={{ marginTop: 6 }}>
            {when} · {room.doctor_name}
          </p>
        </div>
        <Link className="button ghost" href="/portal">
          Back to portal
        </Link>
      </div>

      {room.room_url ? (
        <div
          className="card"
          style={{ marginTop: 22, padding: 0, overflow: 'hidden', height: '70vh', minHeight: 420 }}
        >
          <iframe
            src={room.room_url}
            title="Video consult"
            allow="camera; microphone; fullscreen; display-capture; autoplay"
            style={{ width: '100%', height: '100%', border: 'none' }}
          />
        </div>
      ) : (
        <p className="pill overdue" style={{ marginTop: 22 }}>
          This booking was made for a clinic visit, not a video consult.
        </p>
      )}

      <p className="fine" style={{ marginTop: 14 }}>
        Video runs on a keyless demo room. Before launch this switches to a managed provider with
        recording and consent handling.
      </p>
    </main>
  );
}
