import { redirect } from 'next/navigation';

/**
 * The PRD publishes passports at pawcare.id/pet/[slug], which is the link parents
 * receive. The rendered page lives at /p/[slug], so this keeps the documented
 * address working without a second copy.
 */
export default async function PetPassportAlias({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  redirect(`/p/${slug}`);
}
