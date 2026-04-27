import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata = {
  title: "SNT-FOS",
  description: "SNT Holdings Financial Operating System",
};

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/transactions", label: "Journal" },
  { href: "/accounts", label: "Accounts" },
  { href: "/counterparties", label: "Counterparties" },
  { href: "/tax", label: "Tax Calendar" },
  { href: "/documents", label: "Documents" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased">
        <header className="border-b border-steel-100 bg-white">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm tracking-widest text-ink">SNT · FOS</span>
              <span className="text-xs text-steel-500">Financial Operating System</span>
            </div>
            <nav className="flex gap-6 text-sm text-steel-700">
              {NAV.map((n) => (
                <Link key={n.href} href={n.href} className="hover:text-ink">
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
