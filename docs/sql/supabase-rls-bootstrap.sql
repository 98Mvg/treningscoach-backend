-- Coachi Supabase bootstrap for user-owned tables on the existing schema.
-- Apply after the SQLAlchemy/Alembic schema has been migrated to Supabase Postgres.

alter table public.users enable row level security;
alter table public.workout_history enable row level security;
alter table public.coaching_scores enable row level security;
alter table public.user_subscriptions enable row level security;

drop policy if exists "users_self_select" on public.users;
create policy "users_self_select"
on public.users
for select
using (auth.uid()::text = id);

drop policy if exists "users_self_update" on public.users;
create policy "users_self_update"
on public.users
for update
using (auth.uid()::text = id)
with check (auth.uid()::text = id);

drop policy if exists "workout_history_self_access" on public.workout_history;
create policy "workout_history_self_access"
on public.workout_history
for all
using (auth.uid()::text = user_id)
with check (auth.uid()::text = user_id);

drop policy if exists "coaching_scores_self_access" on public.coaching_scores;
create policy "coaching_scores_self_access"
on public.coaching_scores
for all
using (auth.uid()::text = user_id)
with check (auth.uid()::text = user_id);

drop policy if exists "user_subscriptions_self_access" on public.user_subscriptions;
create policy "user_subscriptions_self_access"
on public.user_subscriptions
for all
using (auth.uid()::text = user_id)
with check (auth.uid()::text = user_id);
