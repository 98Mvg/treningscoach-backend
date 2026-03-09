import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';
import { Providers } from '@/components/providers';

export const metadata: Metadata = {
  title: 'Coachi',
  description: 'Coachi is your real-time running coach with deterministic workout guidance, audio cues, and a clean path to premium intelligence.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <main>
            <div className="page-shell">
              <nav className="nav">
                <Link className="brand" href="/">Coachi</Link>
                <div className="nav-links">
                  <Link href="/account">Account</Link>
                  <Link href="/sign-in">Sign in</Link>
                  <Link href="/support">Support</Link>
                  <Link href="/legal/privacy">Privacy</Link>
                  <Link href="/legal/terms">Terms</Link>
                </div>
              </nav>
              {children}
              <footer className="footer">
                <div>Coachi.no</div>
                <div>Deterministic workout coaching stays on the current Flask runtime during this migration.</div>
              </footer>
            </div>
          </main>
        </Providers>
      </body>
    </html>
  );
}
