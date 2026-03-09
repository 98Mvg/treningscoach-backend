import Link from 'next/link';

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <span className="kicker">Coachi.no foundation</span>
        <h1>Your running coach, without product drift.</h1>
        <p>
          Coachi keeps the current deterministic workout engine intact while adding the business platform layers that make launch,
          support, account access, analytics, and future monetization practical.
        </p>
        <div className="cta-row">
          <Link className="button primary" href="/account">Open account shell</Link>
          <Link className="button secondary" href="/support">Support and legal</Link>
        </div>
      </section>

      <section className="grid two">
        <article className="card">
          <h2>What stays unchanged</h2>
          <p className="muted">
            The iPhone workout runtime, Flask backend, audio packs, and deterministic event selection remain on the existing path.
          </p>
        </article>
        <article className="card">
          <h2>What gets added</h2>
          <p className="muted">
            A Next.js surface for Coachi.no, Supabase as the long-term data home, Clerk for future identity, and observability from day 1.
          </p>
        </article>
      </section>

      <section className="card" style={{ marginTop: 32 }}>
        <h2>Launch-minded product rules</h2>
        <table className="table">
          <tbody>
            <tr><th>Workout engine</th><td>Keep the current Flask + zone_event_motor path</td></tr>
            <tr><th>Identity target</th><td>Clerk, with additive migration</td></tr>
            <tr><th>Data target</th><td>Supabase Postgres</td></tr>
            <tr><th>iOS billing</th><td>StoreKit first</td></tr>
            <tr><th>Web billing</th><td>Stripe later, not Phase 1</td></tr>
            <tr><th>Analytics</th><td>PostHog from day 1</td></tr>
            <tr><th>Error tracking</th><td>Sentry from day 1</td></tr>
          </tbody>
        </table>
      </section>
    </>
  );
}
