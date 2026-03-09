import { headers } from 'next/headers';
import { NextResponse } from 'next/server';
import { Webhook } from 'svix';
import { serverEnv } from '@/lib/env';
import { clearClerkUserLink, type ClerkUserPayload, upsertClerkUserProfile } from '@/lib/clerk-sync';

type ClerkWebhookEvent = {
  type: 'user.created' | 'user.updated' | 'user.deleted' | string;
  data: ClerkUserPayload | { id: string };
};

export const dynamic = 'force-dynamic';

function requireWebhookSecret(): string {
  if (!serverEnv.CLERK_WEBHOOK_SECRET) {
    throw new Error('CLERK_WEBHOOK_SECRET is not configured');
  }

  return serverEnv.CLERK_WEBHOOK_SECRET;
}

export async function POST(req: Request) {
  try {
    const secret = requireWebhookSecret();
    const headerStore = await headers();
    const svixId = headerStore.get('svix-id');
    const svixTimestamp = headerStore.get('svix-timestamp');
    const svixSignature = headerStore.get('svix-signature');

    if (!svixId || !svixTimestamp || !svixSignature) {
      return NextResponse.json({ error: 'Missing Svix headers' }, { status: 400 });
    }

    const payload = await req.text();
    const webhook = new Webhook(secret);
    const event = webhook.verify(payload, {
      'svix-id': svixId,
      'svix-timestamp': svixTimestamp,
      'svix-signature': svixSignature
    }) as ClerkWebhookEvent;

    if (event.type == 'user.created' || event.type == 'user.updated') {
      await upsertClerkUserProfile(event.data as ClerkUserPayload);
    } else if (event.type == 'user.deleted') {
      const deleted = event.data as { id: string };
      if (deleted.id) {
        await clearClerkUserLink(deleted.id);
      }
    }

    return NextResponse.json({ received: true, type: event.type });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown Clerk webhook error';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
