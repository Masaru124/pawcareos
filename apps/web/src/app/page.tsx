import Image from 'next/image';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { currentPrincipal } from '@/lib/principal';

const proof = [
  { value: '20 s', label: 'exam table to signed prescription' },
  { value: '3 doors', label: 'one per role, no shared dashboard' },
  { value: '1 link', label: 'vaccines, doses and the next due date' },
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

const chapters = [
  {
    photo: '/photos/cat-exam.jpg',
    width: 1184,
    height: 880,
    alt: 'A veterinarian listening to a grey cat’s chest with a stethoscope',
    title: 'Prescribe while the dog is still on the table',
    body: 'Weight, diagnosis and three drugs on one keyboard-first screen. The code prints once and never changes, so the bottle in the parent’s hand and the row in the record always agree.',
    points: ['Keyboard-first, one screen', 'Signed and locked on issue', 'Allergies surfaced before the dose'],
  },
  {
    photo: '/photos/parent-phone.jpg',
    width: 1248,
    height: 832,
    alt: 'A pet parent holding a phone while a brown dog rests beside her',
    title: 'A passport the parent opens in the chat',
    body: 'Every visit ends with the prescription and a public passport page. No app install, no login, no PDF hunting — the booster date is on the same page as the medicine.',
    points: ['One link per pet, no account', 'Vaccines with due dates', 'Next visit already on the card'],
  },
];

export default async function HomePage() {
  const principal = await currentPrincipal();
  if (principal) redirect(principal.home);

  return (
    <main className="landing">
      <section className="hero">
        <div className="wrap hero-inner">
          <div className="hero-copy">
            <h1>
              The <span className="nobreak">20-second</span> prescription.
            </h1>
            <p className="hero-lede">
              PawCare OS ends the visit properly: a signed prescription, a WhatsApp passport, and a
              booster reminder parents actually answer. Three roles, three rooms — nobody squints at
              somebody else’s screen.
            </p>
            <div className="hero-actions">
              <Link className="button large" href="/login">
                Open the clinic
              </Link>
              <Link className="button ghost large" href="/find-a-vet">
                Book a visit
              </Link>
            </div>
            <p className="hero-fine">
              Runs on the receptionist’s laptop and the doctor’s phone. No install.
            </p>
          </div>

          <figure className="hero-frame">
            <Image
              src="/photos/exam.jpg"
              alt="A veterinarian in green scrubs examining a golden retriever on the exam table"
              width={1248}
              height={832}
              priority
              sizes="(max-width: 900px) 100vw, 46vw"
            />
            <figcaption className="hero-ticket">
              <span className="hero-ticket-time">Today · 10:30</span>
              <strong>Bruno · Golden Retriever</strong>
              <span className="hero-ticket-sub">Booster review with Dr. Rao</span>
              <span className="pill valid">arrived</span>
            </figcaption>
          </figure>
        </div>
      </section>

      <section className="statement">
        <div className="wrap statement-inner">
          <h2 className="statement-line">
            Fourteen boosters are due this month. <em>All fourteen were asked, four are booked.</em>
          </h2>
          <dl className="proof">
            {proof.map((item) => (
              <div key={item.value}>
                <dt>{item.value}</dt>
                <dd>{item.label}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="wrap doors">
        <h2 className="section-title">Everyone gets the page they need</h2>
        <ul className="door-list">
          {doors.map((door) => (
            <li key={door.role}>
              <Link className="door-row" href={door.href}>
                <span className="door-role">{door.role}</span>
                <span className="door-text">
                  <strong>{door.title}</strong>
                  <span>{door.body}</span>
                </span>
                <span className="door-go" aria-hidden="true">
                  →
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section className="chapter">
        <div className="wrap chapter-inner">
          <div className="chapter-copy">
            <h2 className="section-title">The clinic, not a dashboard</h2>
            <p className="chapter-body">
              One Saturday morning, four people, four screens that agree with each other. The board
              the owner reads is the list the front desk works and the day the doctor is actually
              having.
            </p>
            <ul className="chapter-list">
              <li>Walk-ins appear on the board the moment they land</li>
              <li>Check-in moves the row, it does not open a second one</li>
              <li>Every action is signed with who did it and when</li>
            </ul>
          </div>
          <figure className="chapter-photo wide">
            <Image
              src="/photos/reception.jpg"
              alt="The reception desk of a small veterinary clinic in morning light"
              width={1248}
              height={832}
              sizes="(max-width: 900px) 100vw, 48vw"
            />
          </figure>
        </div>
      </section>

      {chapters.map((chapter, index) => (
        <section className="chapter" key={chapter.title}>
          <div className={`wrap chapter-inner${index % 2 === 1 ? ' flipped' : ''}`}>
            <div className="chapter-copy">
              <h2 className="section-title">{chapter.title}</h2>
              <p className="chapter-body">{chapter.body}</p>
              <ul className="chapter-list">
                {chapter.points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
            <figure className="chapter-photo">
              <Image
                src={chapter.photo}
                alt={chapter.alt}
                width={chapter.width}
                height={chapter.height}
                sizes="(max-width: 900px) 100vw, 48vw"
              />
            </figure>
          </div>
        </section>
      ))}

      <section className="wrap cta">
        <div className="cta-band">
          <div>
            <h2>One clinic, one Saturday morning.</h2>
            <p>
              Fourteen boosters are due this month. Walk the demo clinic and watch the day fill
              itself.
            </p>
          </div>
          <div className="cta-actions">
            <Link className="button inverse large" href="/find-a-vet">
              Book a visit
            </Link>
            <Link className="button ghost inverse large" href="/login">
              Sign in
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
