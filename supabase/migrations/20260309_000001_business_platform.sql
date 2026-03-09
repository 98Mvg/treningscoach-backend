create extension if not exists pgcrypto;

create table if not exists profiles (
    id uuid primary key default gen_random_uuid(),
    clerk_user_id text unique,
    legacy_user_id text unique,
    email text,
    language text,
    training_level text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists workout_sessions (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references profiles(id) on delete cascade,
    legacy_session_id text unique,
    started_at timestamptz,
    ended_at timestamptz,
    workout_type text,
    device text,
    notes text,
    created_at timestamptz not null default now()
);

create table if not exists workout_metrics (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null references workout_sessions(id) on delete cascade,
    coaching_score integer,
    avg_hr integer,
    zones_json jsonb,
    summary_json jsonb,
    created_at timestamptz not null default now()
);

create table if not exists entitlements (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references profiles(id) on delete cascade,
    is_pro boolean not null default false,
    source text not null,
    status text not null,
    current_period_end timestamptz,
    premium_talk_to_coach boolean not null default false,
    premium_extended_history boolean not null default false,
    premium_advanced_analysis boolean not null default false,
    premium_multiple_coaches boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists identity_links (
    id uuid primary key default gen_random_uuid(),
    legacy_user_id text not null unique,
    clerk_user_id text not null unique,
    created_at timestamptz not null default now()
);

create table if not exists email_events (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid references profiles(id) on delete set null,
    template text not null,
    recipient_email text,
    provider text not null default 'resend',
    provider_message_id text,
    sent_at timestamptz not null default now(),
    metadata_json jsonb not null default '{}'::jsonb
);

create index if not exists idx_profiles_email on profiles(email);
create index if not exists idx_workout_sessions_profile_id on workout_sessions(profile_id);
create index if not exists idx_workout_metrics_session_id on workout_metrics(session_id);
create index if not exists idx_entitlements_profile_id on entitlements(profile_id);
create index if not exists idx_email_events_profile_id on email_events(profile_id);
