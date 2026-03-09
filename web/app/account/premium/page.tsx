import { auth } from '@clerk/nextjs/server';
import { getAccountDataSnapshot } from '@/lib/account-data';

export default async function AccountPremiumPage() {
  const { userId } = await auth();
  const snapshot = await getAccountDataSnapshot(userId);
  const entitlement = snapshot.entitlement;

  return (
    <section className="card">
      <span className="kicker">Entitlement shell</span>
      <h1>Premium status</h1>
      <p className="muted">
        Premium access is modeled in the data layer and unlocked from iOS with StoreKit first. Stripe is reserved for later web billing.
      </p>
      {snapshot.warnings.length > 0 ? (
        <div className="notice" style={{ marginTop: 16 }}>
          {snapshot.warnings.map((warning) => (
            <div key={warning}>{warning}</div>
          ))}
        </div>
      ) : null}
      <div className="grid two" style={{ marginTop: 20 }}>
        <article className="card">
          <h2>Current plan</h2>
          <p className="muted">{entitlement?.is_pro ? 'Pro is active for this account.' : 'This account is currently on the free tier.'}</p>
          <div><strong>Status:</strong> {entitlement?.status ?? 'inactive'}</div>
          <div><strong>Source:</strong> {entitlement?.source ?? 'storekit (expected later)'}</div>
          <div><strong>Current period end:</strong> {entitlement?.current_period_end ?? 'Not available'}</div>
        </article>
        <article className="card">
          <h2>Feature flags</h2>
          <ul className="flag-list">
            <li>Talk to Coach: {entitlement?.premium_talk_to_coach ? 'enabled' : 'free/limited'}</li>
            <li>Extended history: {entitlement?.premium_extended_history ? 'enabled' : 'disabled'}</li>
            <li>Advanced analysis: {entitlement?.premium_advanced_analysis ? 'enabled' : 'disabled'}</li>
            <li>Multiple coaches: {entitlement?.premium_multiple_coaches ? 'enabled' : 'disabled'}</li>
          </ul>
        </article>
      </div>
    </section>
  );
}
