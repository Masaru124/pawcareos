import Link from 'next/link';
import { redirect } from 'next/navigation';

import { currentPrincipal } from '@/lib/principal';

const proof = [
  { value: '20 s', label: 'from exam table to signed prescription' },
  { value: '3 doors', label: 'one per role, no shared dashboard' },
  { value: '1 link', label: 'carrying vaccines, doses and the next due date' },
];

const features = [
  {
    title: 'Prescribe while the dog is still on the table',
    body: 'Weight, diagnosis and three drugs on one keyboard-first screen. The code prints once and never changes.',
  },
  {
    title: 'A passport the parent opens in the chat',
    body: 'Every visit ends with the prescription and a public passport page. No app install, no login, no PDF hunting.',
  },
  {
    title: 'Recall that books instead of nagging',
    body: 'A week before a booster is due the parent gets one message with three buttons. Confirm books the slot. Stop means stop.',
  },
];

const doors = [
  {
    role: 'Owner',
    title: 'Operations',
    body: 'Today’s board, the team, invites and everything the clinic did.',
    href: '/login',
  },
  {
    role: 'Doctor',
    title: 'Your clinical day',
    body: 'Only your appointments, with allergies and history attached.',
    href: '/login',
  },
  {
    role: 'Front desk',
    title: 'Arrivals',
    body: 'Who is due, who has arrived, who has been seen. One tap each.',
    href: '/login',
  },
  {
    role: 'Pet parent',
    title: 'The passport',
    body: 'Records, next visit and the booster that is coming up.',
    href: '/login?as=parent',
  },
];

export default async function HomePage() {
  const principal = await currentPrincipal();
  if (principal) redirect(principal.home);

  return (
    <main>
      <section className="wrap landing-hero">
        <div>
          <p className="eyebrow">For independent veterinary clinics</p>
          <h1>The 20-second prescription.</h1>
          <p className="lede">
            PawCare OS ends the visit properly: a signed prescription, a WhatsApp passport, and a
            booster reminder parents actually answer. Three roles, three rooms — nobody squints at
            somebody else’s screen.
          </p>
          <div className="hero-actions">
            <Link className="button" href="/login">
              Open the clinic
            </Link>
            <Link className="button ghost" href="/find-a-vet">
              Find a vet
            </Link>
            <Link className="button quiet" href="/login?as=parent">
              I’m a pet parent
            </Link>
          </div>
          <p className="fine">
            Runs on the receptionist’s laptop and the doctor’s phone. No install.
          </p>
        </div>

        <aside className="hero-aside" aria-label="The clinic day at a glance">
          <div className="hero-aside-head">
            <span className="dot-live" aria-hidden="true" />
            <span>Saturday · 09:00–18:00</span>
          </div>
          <ol className="hero-list">
            <li>
              <time>10:30</time>
              <span>
                <strong>Bruno</strong> · Golden Retriever
                <em>Booster review</em>
              </span>
              <span className="pill valid">arrived</span>
            </li>
            <li>
              <time>11:00</time>
              <span>
                <strong>Milo</strong> · Indie
                <em>Skin consult</em>
              </span>
              <span className="pill neutral">due</span>
            </li>
            <li>
              <time>11:30</time>
              <span>
                <strong>Cleo</strong> · Persian
                <em>Online follow-up</em>
              </span>
              <span className="pill due_soon">video</span>
            </li>
          </ol>
          <p className="fine hero-aside-foot">Every row is one tap away from the record.</p>
        </aside>
      </section>

      <section className="wrap">
        <div className="proof-strip">
          {proof.map((item) => (
            <div key={item.value}>
              <div className="proof-value">{item.value}</div>
              <p className="fine">{item.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="wrap section">
        <div className="section-head">
          <p className="eyebrow">Signing in</p>
          <h2>Everyone gets the page they need</h2>
        </div>
        <div className="door-grid">
          {doors.map((door) => (
            <Link key={door.role} className="door" href={door.href}>
              <span className="pill neutral">{door.role}</span>
              <h3>{door.title}</h3>
              <p className="muted">{door.body}</p>
              <span className="door-go">Sign in →</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="wrap section">
        <div className="section-head">
          <p className="eyebrow">What changes on Monday</p>
          <h2>A clinic record that finishes the job</h2>
        </div>
        <div className="feature-grid">
          {features.map((feature, index) => (
            <article key={feature.title} className="card feature-card">
              <p className="mono feature-index">0{index + 1}</p>
              <h3>{feature.title}</h3>
              <p className="muted">{feature.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="wrap section">
        <div className="cta-band">
          <div>
            <h2>One clinic, one Saturday morning.</h2>
            <p>
              Fourteen boosters are due this month. Walk the demo clinic and watch the day fill
              itself.
            </p>
          </div>
          <div className="cta-actions">
            <Link className="button inverse" href="/find-a-vet">
              Book a visit
            </Link>
            <Link className="button ghost inverse" href="/login">
              Sign in
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
