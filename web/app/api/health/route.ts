import { NextResponse } from 'next/server';
import { publicEnv, serverEnv } from '@/lib/env';

export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    siteUrl: publicEnv.NEXT_PUBLIC_SITE_URL,
    services: {
      clerk: Boolean(publicEnv.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && serverEnv.CLERK_SECRET_KEY),
      supabase: Boolean(serverEnv.SUPABASE_URL && serverEnv.SUPABASE_ANON_KEY && serverEnv.SUPABASE_SERVICE_ROLE_KEY),
      posthog: Boolean(publicEnv.NEXT_PUBLIC_POSTHOG_KEY && publicEnv.NEXT_PUBLIC_POSTHOG_HOST),
      sentry: Boolean(publicEnv.NEXT_PUBLIC_SENTRY_DSN),
      resend: Boolean(serverEnv.RESEND_API_KEY)
    }
  });
}
