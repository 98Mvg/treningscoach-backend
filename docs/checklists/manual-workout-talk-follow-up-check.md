# Manual Check: Workout Talk Follow-Up

Purpose: verify that short follow-up questions during an active workout stay on the workout Q&A path and use recent context.

## Preconditions

- App build includes the zone-event priority and workout-talk follow-up changes.
- Backend is reachable.
- User is signed in, or the backend currently accepts the workout session in guest mode.
- Use an intervals workout so `reps_remaining_including_current` and `time_left_s` are available.

## Steps

1. Launch the iPhone app.
2. Start an intervals workout from [WorkoutLaunchView.swift](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Views/Tabs/WorkoutLaunchView.swift).
3. Wait until the workout is active and at least one deterministic coach event has fired.
4. Tap `Talk to Coach` and ask: `How many intervals are left?`
5. Wait for the coach answer to finish.
6. Tap `Talk to Coach` again and ask: `And how long`

## Expected Result

- The second request is handled as workout Q&A, not generic chat.
- The answer stays workout-relevant.
- The answer can refer to remaining intervals and/or time left.
- The answer does not get blocked as off-topic.
- Continuous coaching still resumes normally after the talk exchange.

## Useful Logs

- Backend:
  - `Coach talk request trigger=button context=workout`
  - no `TALK_POLICY category=off_topic blocked=true`
- iOS:
  - `EVENT_SELECTED ... selection_source=backend_primary` or `selection_source=backend_order`
  - no unexpected talk arbitration loop after the reply finishes

## Failure Indicators

- Second prompt returns a refusal line from talk policy.
- Second prompt gets a generic non-workout answer.
- iOS suppresses the next deterministic workout event after the talk response for longer than the normal collision window.
