import { ensurePostHogInitialized } from '@/lib/posthog';

export function register() {
  ensurePostHogInitialized();
}
