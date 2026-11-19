import type { ReactNode } from 'react';
import Link from 'next/link';

import { SiteHeader } from '@/components/SiteHeader';
import { currentPrincipal } from '@/lib/principal';

import './globals.css';

export const metadata = {
  title: 'PawCare OS — the 20-second prescription',
  description: 'Clinical records, a WhatsApp pet passport and booster recall for independent veterinary clinics.',
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const principal = await currentPrincipal();

  return (
    <html lang="en">
      <body>
        <SiteHeader principal={principal} />
        {children}
        <footer className="site-footer">
          <div className="wrap footer-inner">
            <span>PawCare OS · Bengaluru</span>
            <span>WhatsApp delivery runs in demo mode until your Meta templates are approved.</span>
            <Link href="/find-a-vet">Find a vet</Link>
          </div>
        </footer>
      </body>
    </html>
  );
}
