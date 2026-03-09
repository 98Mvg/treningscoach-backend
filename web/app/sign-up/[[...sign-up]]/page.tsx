import { SignUp } from '@clerk/nextjs';

export default function SignUpPage() {
  return (
    <section className="card">
      <span className="kicker">Identity shell</span>
      <h1>Create your Coachi account</h1>
      <p className="muted">
        Web identity is being added around the existing product. The deterministic workout runtime and current mobile auth stay intact during migration.
      </p>
      <div style={{ marginTop: 24 }}>
        <SignUp />
      </div>
    </section>
  );
}
