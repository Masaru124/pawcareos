import Link from 'next/link';
import { redirect } from 'next/navigation';

import { ParentJoinForm } from '@/components/ParentJoinForm';
import { currentPrincipal } from '@/lib/principal';
import { sessionEmail } from '@/lib/session';

export default async function ParentJoinPage() {
  const principal = await currentPrincipal();
  if (principal) redirect(principal.home);

  const email = await sessionEmail();
  if (!email) redirect('/login');

  return (
    <main className="wrap" style={{ paddingTop: 48, maxWidth: 460 }}>
      <p className="label">One step left</p>
      <h1 style={{ fontSize: 34 }}>Your pet parent portal.</h1>
      <p className="muted" style={{ marginTop: 10 }}>
        You’re verified as <span className="mono">{email}</span>. Add your name and the phone
        number your clinic knows, and your pets’ records appear here.
      </p>

      <div className="card" style={{ padding: '26px 24px', marginTop: 26 }}>
        <ParentJoinForm />
      </div>

      <p className="fine" style={{ marginTop: 18 }}>
        Booking something instead? <Link href="/find-a-vet">Find a vet</Link>.{' '}
        <a href="/logout">Sign out</a>.
      </p>
    </main>
  );
}
