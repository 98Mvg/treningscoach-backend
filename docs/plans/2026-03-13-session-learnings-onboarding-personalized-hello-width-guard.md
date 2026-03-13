# Session learnings: personalized hello width guard

- The personalized `Hello! {name}` onboarding step drifted from the shared onboarding width rules because it used raw `maxWidth` headline constraints instead of the repo's existing `layoutWidth -> contentWidth -> textWidth` clamp pattern.
- Full-screen hero onboarding screens need an explicit text-width clamp even when the outer container is already clamped; otherwise the text block still feels too wide on narrower iPhones.
- Guardrail added:
  - `DataPurposeStepView` now derives `textWidth` from `contentWidth`
  - the two hero text blocks use `frame(width: textWidth, alignment: .leading)`
  - source contract covers the personalized hello page so width regressions are caught before device testing
