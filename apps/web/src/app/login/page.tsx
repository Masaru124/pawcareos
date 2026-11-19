import Link from 'next/link';

import { LoginForm } from '@/components/LoginForm';
import { currentPrincipal } from '@/lib/principal';
import { sessionEmail } from '@/lib/session';

const copy = {
  clinic: {
    eyebrow: 'Clinic sign in',
    title: 'Back to the table.',
    body: 'For owners, doctors and reception. Your clinic invites the address; the first sign-in claims it.',
  },
  parent: {
    eyebrow: 'Pet parent sign in',
    title: 'Your pet’s records.',
    body: 'Passports, vaccination dates, prescriptions and video consults. Ask your clinic to add this email to your family record.',
  },
} as const;

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; as?: string }>;
}) {
  const { error, as } = await searchParams;
  const role = as === 'parent' ? 'parent' : 'clinic';
  const text = copy[role];
  const principal = await currentPrincipal();

  // Signed in already? The form becomes the way out, not another way in.
  if (principal) {
    const email = await sessionEmail();
    const landing = {
      owner: 'operations',
      doctor: 'my day',
      receptionist: 'the front desk',
      parent: 'my pets',
    }[principal.role];
    return (
      <main className="wrap" style={{ paddingTop: 48, maxWidth: 460 }}>
        <p className="eyebrow">Already signed in</p>
        <h1 style={{ fontSize: 34 }}>You’re in.</h1>
        <p className="muted" style={{ marginTop: 10 }}>
          {principal.name}
          {email ? ` · ${email}` : ''}
        </p>

        <div className="card" style={{ padding: '26px 24px', marginTop: 26 }}>
          <p className="muted" style={{ fontSize: 15 }}>
            Sign out first if you need to use a different address on this browser.
          </p>
          <div style={{ display: 'flex', gap: 10, marginTop: 18, flexWrap: 'wrap' }}>
            <Link className="button" href={principal.home}>
              Open {landing}
            </Link>
            <a className="button ghost" href="/logout">
              Sign out
            </a>
          </div>
        </div>
      </main>
    );
  }
  const configured = Boolean(
    (process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL) &&
      (process.env.SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY),
  );

  return (
    <main className="wrap" style={{ paddingTop: 48, maxWidth: 460 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 26 }}>
        <Link
          className={role === 'clinic' ? 'button' : 'button ghost'}
          href="/login"
          style={{ padding: '7px 14px' }}
        >
          Clinic staff
        </Link>
        <Link
          className={role === 'parent' ? 'button' : 'button ghost'}
          href="/login?as=parent"
          style={{ padding: '7px 14px' }}
        >
          Pet parent
        </Link>
      </div>

      <p className="eyebrow">{text.eyebrow}</p>
      <h1 style={{ fontSize: 34 }}>{text.title}</h1>
      <p className="muted" style={{ marginTop: 10 }}>
        {text.body}
      </p>

      {error && (
        <p className="pill overdue" role="alert" style={{ marginTop: 18 }}>
          {error}
        </p>
      )}

      {configured ? (
        <div className="card" style={{ padding: '26px 24px', marginTop: 26 }}>
          <a
            className="button"
            href="/api/session/google"
            style={{ width: '100%', background: '#f4efe2', color: 'var(--ink)', borderColor: 'var(--line)' }}
          >
            <span aria-hidden style={{ fontWeight: 700 }}>G</span> Continue with Google
          </a>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              margin: '22px 0',
              color: 'var(--ink-faint)',
              fontSize: 12,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
            or
            <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
          </div>

          <LoginForm />
        </div>
      ) : (
        <div className="card" style={{ padding: '26px 24px', marginTop: 26 }}>
          <h2 style={{ fontSize: 20 }}>Supabase is not connected yet</h2>
          <p className="muted" style={{ marginTop: 10, fontSize: 15 }}>
            PawCare OS uses Supabase Auth for Google, passwords and phone OTP. Add these two values
            to <span className="mono"> apps/web/.env.local</span> and restart the dev server.
          </p>
          <pre
            className="mono"
            style={{
              background: 'var(--canvas-deep)',
              padding: 14,
              borderRadius: 10,
              marginTop: 14,
              overflowX: 'auto',
            }}
          >
            {`SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon key>`}
          </pre>
        </div>
      )}

      <p className="fine" style={{ marginTop: 18 }}>
        Looking for a vet instead? <Link href="/find-a-vet">Book without an account</Link>.
      </p>
    </main>
  );
}
