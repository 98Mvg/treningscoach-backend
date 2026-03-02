# Coachi Website Quality Map (Mia-inspired, Coachi-differentiated)

## 1) Business goals
- Increase qualified waitlist conversion from homepage traffic.
- Increase demo completion (mic granted + at least one coaching response).
- Improve trust signals early (health status, provider status, wearable compatibility).
- Communicate freemium-to-premium value clearly.

## 2) Primary user flows
- Flow A (new visitor): Hero -> How it works -> Features -> Pricing -> Waitlist submit.
- Flow B (high-intent visitor): Hero -> Live demo -> Talk to coach -> Waitlist submit.
- Flow C (skeptical visitor): Hero status cards -> Wearable compatibility -> FAQ -> Waitlist.

## 3) Positioning strategy
- Keep Mia-like visual clarity and premium polish.
- Differentiate with product truth: real-time voice loop, not static claims.
- Convert trust into action with live proof and clean CTA path.

## 4) UI system decisions
- Visual direction: light premium surface + deep purple brand anchors.
- Typography: Poppins for headlines, Manrope for readable body copy.
- Layout: large rounded cards, soft shadows, high contrast CTA hierarchy.
- Motion: restrained micro-interactions (lift on hover, pulse on live orb).

## 5) Conversion architecture
- Hero: clear value promise + dual CTA (demo first, app second).
- Mid-page: explainability sections that mirror app logic (measure -> decide -> coach).
- Bottom: pricing clarity + waitlist form + app store entry.
- Footer: utility links + operational proof endpoints.

## 6) Trust layer
- Dynamic status badges from /health and /brain/health.
- Wearable compatibility callout: Garmin, Polar, Fitbit, Apple Watch.
- Runtime telemetry in live demo to make behavior observable.

## 7) Experiment plan (A/B over 2-3 weeks)
- Test A: Hero headline angle (performance vs health longevity).
- Test B: Primary CTA text ("Start live demo" vs "Try Coachi now").
- Test C: Pricing block order (premium-first vs free-first).
- Test D: Waitlist placement (mid-page vs bottom-only).

## 8) KPI dashboard (minimum)
- Unique visitors.
- Waitlist submit rate.
- Demo start rate.
- Mic permission rate.
- First coaching response rate.
- Talk-to-coach usage rate.

## 9) Next implementation steps
- Replace placeholder app-store links with final store URLs.
- Add real partner/wearable logos assets to improve perceived quality.
- Add server-side waitlist persistence (DB) instead of in-memory list.
- Add event aggregation endpoint or analytics pipeline for funnel monitoring.
