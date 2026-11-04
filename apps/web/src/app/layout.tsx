import type { Metadata } from "next";
import { Fraunces, Source_Sans_3 } from "next/font/google";
import { AuthSessionSync } from "@/components/auth-session-sync";
import "./globals.css";

const display = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const sans = Source_Sans_3({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "My Cricket 360",
    template: "%s · My Cricket 360",
  },
  description:
    "Multi-club cricket management for Starks Cricket and CGI Steelers Cricket.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${display.variable} ${sans.variable} font-sans-body antialiased`}
      >
        <AuthSessionSync />
        {children}
      </body>
    </html>
  );
}
