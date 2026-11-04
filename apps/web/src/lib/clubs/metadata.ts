import type { Metadata } from "next";
import { canonicalOrigin } from "@/lib/clubs";
import { getResolvedHost } from "@/lib/clubs/server";

export async function clubPageMetadata(
  path: string,
  title: string,
  description: string,
): Promise<Metadata> {
  const resolved = await getResolvedHost();
  if (resolved.kind !== "club") {
    return { title, robots: { index: false, follow: false } };
  }
  const origin = canonicalOrigin(resolved);
  const url = origin ? `${origin}${path}` : undefined;
  return {
    title: `${title} · ${resolved.club.name}`,
    description,
    alternates: url ? { canonical: url } : undefined,
    openGraph: {
      title: resolved.club.name,
      description,
      url,
      siteName: resolved.club.name,
    },
  };
}
