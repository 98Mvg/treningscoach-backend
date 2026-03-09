import Link from 'next/link';
import { auth, currentUser } from '@clerk/nextjs/server';
import { getAccountDataSnapshot } from '@/lib/account-data';

export default async function AccountPage() {
  const { userId } = await auth();
  const user = userId ? await currentUser() : null;
  const email = user?.primaryEmailAddress?.emailAddress ?? user?.emailAddresses?.[0]?.emailAddress ?? 'Signed in via Clerk';
  const snapshot = await getAccountDataSnapshot(userId);

  return (
    <>
      <section className="card">
        <span className="kicker">Account shell</span>
        <h1>Signed-in account surfaces live here.</h1>
        <p className="muted">
          This stays deliberately modest in the migration phase: identity via Clerk, history and entitlements via Supabase, and no parallel
          workout runtime.
        </p>
        <div style={{ marginTop: 16, color: 'var(--muted)' }}>
          <div><strong>Clerk user ID:</strong> {userId ?? 'Unavailable'}</div>
          <div><strong>Email:</strong> {email}</div>
          <div><strong>Linked profile:</strong> {snapshot.profile ? 'Yes' : 'Pending migration'}</div>
          <div><strong>Language:</strong> {snapshot.profile?.language ?? 'Not set'}</div>
          <div><strong>Training level:</strong> {snapshot.profile?.training_level ?? 'Not set'}</div>
          <div><strong>Premium:</strong> {snapshot.entitlement?.is_pro ? 'Active' : 'Free'}</div>
        </div>
        {snapshot.warnings.length > 0 ? (
          <div style={{ marginTop: 16 }} className="notice">
            {snapshot.warnings.map((warning) => (
              <div key={warning}>{warning}</div>
            ))}
          </div>
        ) : null}
      </section>
      <section className="grid three" style={{ marginTop: 24 }}>
        <article className="card">
          <h2>History</h2>
          <p className="muted">{snapshot.workouts.length} mirrored workout sessions are currently available in this account shell.</p>
          <Link className="button secondary" href="/account/history">Open history shell</Link>
        </article>
        <article className="card">
          <h2>Premium</h2>
          <p className="muted">StoreKit-backed entitlement status is normalized into the data layer and shown here.</p>
          <Link className="button secondary" href="/account/premium">Open premium shell</Link>
        </article>
        <article className="card">
          <h2>Preferences</h2>
          <p className="muted">Support and account preferences that are safe to expose on web.</p>
          <Link className="button secondary" href="/account/preferences">Open preferences shell</Link>
        </article>
      </section>
    </>
  );
}
