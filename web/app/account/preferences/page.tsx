import { serverEnv } from '@/lib/env';
import { resendIsConfigured } from '@/lib/email';

export default function AccountPreferencesPage() {
  return (
    <section className="card">
      <span className="kicker">Support shell</span>
      <h1>Preferences and support</h1>
      <p className="muted">
        Keep web account preferences narrow during migration: support, legal entry points, and future communication settings.
      </p>
      <div className="grid two" style={{ marginTop: 20 }}>
        <article className="card">
          <h2>Support</h2>
          <p className="muted">
            Contact: <a href={`mailto:${serverEnv.SUPPORT_EMAIL}`}>{serverEnv.SUPPORT_EMAIL}</a>
          </p>
          <p className="muted">
            Privacy: <a href={`mailto:${serverEnv.PRIVACY_EMAIL}`}>{serverEnv.PRIVACY_EMAIL}</a>
          </p>
        </article>
        <article className="card">
          <h2>Communication status</h2>
          <p className="muted">
            Transactional email provider: {resendIsConfigured() ? 'Resend configured' : 'Resend not configured'}
          </p>
          <p className="muted">
            This page is intentionally limited to safe account and support surfaces while the workout runtime stays on Flask.
          </p>
        </article>
      </div>
    </section>
  );
}
