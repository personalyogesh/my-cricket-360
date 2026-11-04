import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4">
      <h1 className="font-display text-3xl">Not found</h1>
      <p className="mt-3 opacity-80">
        This page is not available for the current club host.
      </p>
      <Link href="/" className="mt-6 underline">
        Back home
      </Link>
    </main>
  );
}
