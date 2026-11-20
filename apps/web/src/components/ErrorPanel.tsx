import Link from 'next/link';

export function ErrorPanel({
  title,
  status,
  detail,
  hint,
}: {
  title: string;
  status?: number;
  detail: string;
  hint?: string;
}) {
  return (
    <div className="card" style={{ padding: '26px 24px', borderColor: 'rgba(155, 47, 47, 0.35)' }}>
      <p className="label" style={{ color: 'var(--rose)', marginBottom: 8 }}>
        {status ? `HTTP ${status}` : 'Request failed'}
      </p>
      <h2 style={{ fontSize: 22 }}>{title}</h2>
      <p style={{ marginTop: 10, color: 'var(--ink-soft)' }}>{detail}</p>
      {hint && (
        <p className="fine" style={{ marginTop: 10 }}>
          {hint}
        </p>
      )}
      <div className="row" style={{ marginTop: 18 }}>
        <Link className="button ghost" href="/login">
          Sign in again
        </Link>
        <Link className="button ghost" href="/">
          Overview
        </Link>
      </div>
    </div>
  );
}
