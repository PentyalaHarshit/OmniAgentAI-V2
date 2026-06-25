import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OmniAgentAI",
  description: "React/Next.js frontend for OmniAgentAI V2"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
