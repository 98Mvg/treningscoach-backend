import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
  return (
    <section className="card">
      <span className="kicker">Identity shell</span>
      <h1>Sign in to Coachi</h1>
      <p className="muted">
        Clerk is the long-term identity provider for Coachi.no. This web shell is additive and does not replace the current iOS auth path.
      </p>
      <div style={{ marginTop: 24 }}>
        <SignIn />
      </div>
    </section>
  );
}
