import { redirect } from 'next/navigation';

import { currentPrincipal } from '@/lib/principal';

/**
 * The old shared board. Every role now has a home built for its own questions,
 * so this path only forwards people who still have it bookmarked.
 */
export default async function QueuePage() {
  const principal = await currentPrincipal();
  redirect(principal?.home ?? '/login');
}
