'use client';

import { ClerkProvider } from '@clerk/nextjs';
import posthog from 'posthog-js';
import { PostHogProvider } from 'posthog-js/react';
import { useEffect } from 'react';
import { ensurePostHogInitialized } from '@/lib/posthog';

function PostHogBootstrap({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    ensurePostHogInitialized();
  }, []);

  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <PostHogBootstrap>{children}</PostHogBootstrap>
    </ClerkProvider>
  );
}
