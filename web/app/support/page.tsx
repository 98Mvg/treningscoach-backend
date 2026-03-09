import { serverEnv } from '@/lib/env';

export default function SupportPage() {
  return (
    <section className="grid two">
      <article className="card">
        <span className="kicker">Support</span>
        <h1>Support and legal entry point</h1>
        <p className="muted">
          Coachi support should stay simple at launch: clear support email, FAQ, legal pages, and no hidden support maze.
        </p>
        <p>
          Support contact: <a href={`mailto:${serverEnv.SUPPORT_EMAIL}`}>{serverEnv.SUPPORT_EMAIL}</a>
        </p>
      </article>
      <article className="card">
        <h2>Recommended launch support flows</h2>
        <ul>
          <li>FAQ in app and on web</li>
          <li>Email-based support</li>
          <li>Clear privacy and terms links</li>
          <li>No misleading premium claims</li>
        </ul>
      </article>
    </section>
  );
}
