# Talk Safety Rules Integration (2026-03-05)

## Scope
- Applies to `/coach/talk` only.
- Applies to all personas in talk mode.
- Does not modify `/coach/continuous` or `zone_event_motor` ownership.

## Enforced categories
- `harassment_bullying`
- `hate_speech`
- `sexual_explicit`
- `harmful_encouragement`
- `off_topic`

## Refusal behavior
- Deterministic policy gate runs before any AI provider routing.
- If blocked, backend returns one localized refusal line from the configured bank.
- Rotation is enabled by default and avoids immediate repeats per `(language, category)`.

### English refusal bank
1. `Lets talk about your workout instead`
2. `I am Your Coach and will only speak about related subjects`
3. `Lets not talk about that`

### Norwegian refusal bank
1. `La oss snakke om din treningsøkt isteden`
2. `Jeg er din Coach og holder meg til relevante temaer.`
3. `La oss ikke snakke om det nå`

## Response metadata
`/coach/talk` now includes:
- `policy_blocked` (bool)
- `policy_category` (string|null)
- `policy_reason` (string|null)

## Runtime logs
- Policy block:
  - `Coach talk policy block trigger=... context=... category=... provider=policy latency_ms=...`
- Normal talk response remains unchanged:
  - `Coach talk response trigger=... latency_ms=... provider=... mode=... fallback_used=...`

## iOS debug visibility
- `WorkoutViewModel` logs:
  - `TALK_POLICY_BLOCKED category=... reason=...`

