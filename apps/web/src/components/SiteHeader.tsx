'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import type { Principal } from '@/lib/principal';

type LinkSpec = { href: string; label: string };

function linksFor(principal: Principal | null): LinkSpec[] {
  if (!principal) {
    return [
      { href: '/find-a-vet', label: 'Find a vet' },
      { href: '/login?as=parent', label: 'Pet parent' },
    ];
  }

  if (principal.kind === 'parent') {
    return [
      { href: '/portal', label: 'My pets' },
      { href: '/find-a-vet', label: 'Find a vet' },
    ];
  }

  const home = { href: principal.home, label: principal.label };
  if (principal.role === 'doctor') {
    return [home, { href: '/patients', label: 'Patients' }];
  }
  if (principal.role === 'receptionist') {
    return [home, { href: '/patients', label: 'Patients' }, { href: '/find-a-vet', label: 'Booking page' }];
  }
  return [
    { href: '/admin', label: 'Operations' },
    { href: '/frontdesk', label: 'Front desk' },
    { href: '/patients', label: 'Patients' },
  ];
}

export function SiteHeader({ principal }: { principal: Principal | null }) {
  const pathname = usePathname();
  const links = linksFor(principal);

  return (
    <header className="site-header">
      <div className="wrap header-inner">
        <Link className="brand" href={principal?.home ?? '/'}>
          <span className="brand-mark" aria-hidden="true">
            PC
          </span>
          <span className="brand-text">
            <strong>PawCare OS</strong>
            <span>{principal ? (principal.kind === 'parent' ? 'Pet passport' : 'Clinic system') : 'Clinic system'}</span>
          </span>
        </Link>

        <nav className="nav" aria-label="Primary">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname === link.href ? 'is-active' : undefined}
              aria-current={pathname === link.href ? 'page' : undefined}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="header-user">
          {principal ? (
            <>
              <span className="header-identity">
                <span className="role-chip">{principal.label}</span>
                <span className="header-name">{principal.name}</span>
              </span>
              <Link className="button ghost small" href="/logout">
                Sign out
              </Link>
            </>
          ) : (
            <Link className="button small" href="/login">
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
