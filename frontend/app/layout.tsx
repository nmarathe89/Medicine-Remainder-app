import "./globals.css";
import type { Metadata } from "next";

// Server component root layout (server + client architecture: this file and
// pages render on the server; interactive pieces are "use client").
export const metadata: Metadata = {
  title: "Mediminder",
  description: "Medicine reminder web app",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
