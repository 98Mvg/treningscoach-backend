import { auth } from '@clerk/nextjs/server';
import { getAccountDataSnapshot } from '@/lib/account-data';

export default async function AccountHistoryPage() {
  const { userId } = await auth();
  const snapshot = await getAccountDataSnapshot(userId);

  return (
    <section className="card">
      <span className="kicker">Supabase-backed shell</span>
      <h1>Workout history</h1>
      <p className="muted">
        This page is reserved for mirrored workout sessions and summary metrics from Supabase. It intentionally does not host a second workout runtime.
      </p>
      {snapshot.warnings.length > 0 ? (
        <div className="notice" style={{ marginTop: 16 }}>
          {snapshot.warnings.map((warning) => (
            <div key={warning}>{warning}</div>
          ))}
        </div>
      ) : null}
      <table className="table" style={{ marginTop: 20 }}>
        <thead>
          <tr>
            <th>Started</th>
            <th>Type</th>
            <th>Device</th>
            <th>Coaching score</th>
            <th>Avg HR</th>
          </tr>
        </thead>
        <tbody>
          {snapshot.workouts.length === 0 ? (
            <tr>
              <td colSpan={5} className="muted">No mirrored workout history is available yet.</td>
            </tr>
          ) : (
            snapshot.workouts.map((workout) => (
              <tr key={workout.id}>
                <td>{workout.started_at ?? 'Unknown'}</td>
                <td>{workout.workout_type ?? 'Unknown'}</td>
                <td>{workout.device ?? 'Unknown'}</td>
                <td>{workout.coaching_score ?? '—'}</td>
                <td>{workout.avg_hr ?? '—'}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
