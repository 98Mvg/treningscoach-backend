# Strategic Brain Integration

## Overview

The Strategic Brain is a Claude-powered high-level coaching intelligence layer that sits **above** the tactical coaching intelligence. It provides strategic guidance, not raw speech.

## Architecture

```
iOS App (Breath Recording)
    ↓
Backend API (/continuous_coach)
    ↓
Breath Analysis (tactical)
    ↓
Coaching Intelligence (should_coach_speak - tactical)
    ↓
Voice Intelligence (should_stay_silent - tactical)
    ↓
Strategic Brain (every 2-3 minutes - strategic)
    ↓
Message Selection (strategic > pattern > config)
    ↓
ElevenLabs TTS (voice generation)
    ↓
Audio Response
```

## Key Design Principles

### ❌ Strategic Brain does NOT:
- Run on every breath (too slow, too expensive)
- Provide raw speech text for every message
- Make tactical breath-by-breath decisions
- Override the fast tactical intelligence

### ✅ Strategic Brain DOES:
- Analyze session trends every 2-3 minutes
- Provide strategic guidance (strategy, tone, message_goal)
- Optionally suggest specific phrasing
- Help calibrate the tactical system
- Generate session summaries

## What Claude Receives

**Structured summaries, NOT raw data:**

```json
{
  "phase": "intense",
  "elapsed": 8,
  "breath_trend": "erratic",
  "avg_tempo": 72,
  "duration_struggling": 92,
  "recent_intensities": ["intense", "intense", "moderate", "intense", "calm"],
  "recent_coaching": ["slow down", "control exhale"],
  "user_experience": "advanced",
  "prefers_silence": true
}
```

## What Claude Returns

**Guidance, NOT speech:**

```json
{
  "strategy": "reduce_overload",
  "tone": "calm_firm",
  "message_goal": "restore_rhythm",
  "suggested_phrase": "Control the exhale. Let the breath settle."
}
```

The system then decides:
- Whether to speak (tactical intelligence still decides)
- When to speak (based on interval and criticality)
- What to say (strategic phrase OR config phrase matching strategy)

## Integration Points

### 1. Initialization (main.py)
```python
from strategic_brain import get_strategic_brain
strategic_brain = get_strategic_brain()  # Singleton instance
```

### 2. Timing Logic (strategic_brain.py)
```python
def should_provide_insight(elapsed_seconds, last_strategic_time, phase):
    # First insight at 2 minutes
    if elapsed_seconds >= 120 and last_strategic_time == 0:
        return True
    # Subsequent insights every 3 minutes
    if elapsed_seconds - last_strategic_time >= 180:
        return True
    return False
```

### 3. Strategic Guidance Request (main.py)
```python
if strategic_brain.should_provide_insight(elapsed_seconds, last_strategic_time, phase):
    strategic_guidance = strategic_brain.get_strategic_insight(
        breath_history=coaching_context["breath_history"],
        coaching_history=coaching_context["coaching_history"],
        phase=phase,
        elapsed_seconds=elapsed_seconds,
        session_context=session_metadata
    )
```

### 4. Message Selection Priority (main.py)
```python
if strategic_guidance and speak_decision:
    # Use Strategic Brain's suggested phrase OR config phrase matching strategy
    coach_text = strategic_guidance.get("suggested_phrase") or get_config_phrase(breath_data, phase)
elif pattern_insight and speak_decision:
    # Use pattern-based insight
    coach_text = pattern_insight
else:
    # Use config phrase
    coach_text = get_coach_response_continuous(breath_data, phase)
```

## Configuration

### Environment Variables (.env)
```bash
# Required for Strategic Brain
ANTHROPIC_API_KEY=your_api_key_here

# Get your key from: https://console.anthropic.com/settings/keys
```

### Timing Configuration (strategic_brain.py)
- First insight: 2 minutes into workout
- Subsequent insights: Every 3 minutes
- Model: claude-3-5-sonnet-20241022
- Max tokens: 200
- Temperature: 0.7

## Testing

### Test Strategic Brain Standalone
```bash
cd backend
export ANTHROPIC_API_KEY="your_key"
python3 strategic_brain.py
```

### Test with Backend
```bash
cd backend
python3 main.py
# Strategic Brain will log when it's available:
# ✅ Strategic Brain (Claude) is available
```

### Monitor Strategic Insights
Watch the logs for:
```
🧠 Requesting strategic guidance from Claude...
✅ Strategic guidance: {'strategy': 'reduce_overload', 'tone': 'calm_firm', ...}
🧠 Using Strategic Brain phrase: Control the exhale. Let the breath settle.
```

## Performance Impact

- **Cost**: ~$0.001 per strategic insight (Claude API)
- **Latency**: 1-2 seconds (async, doesn't block breath analysis)
- **Frequency**: Every 2-3 minutes (low overhead)
- **Total cost per 45-min workout**: ~$0.015 (15 insights)

## Benefits

1. **Strategic Context**: Claude sees the full session picture
2. **Adaptive Coaching**: Adjusts strategy based on trends
3. **Human-like Reasoning**: "They've been struggling for 92 seconds - time to intervene"
4. **Cost-effective**: Only runs occasionally, not every breath
5. **Fast Response**: Tactical system still handles immediate decisions

## Future Enhancements

- Add user profile personalization
- Track coaching effectiveness over sessions
- Adaptive timing based on workout intensity
- Session summaries for post-workout reflection
- Integration with user memory system

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      iOS App (Swift)                        │
│                  Sends 8-second audio chunks                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend API (Flask)                       │
│                  /continuous_coach endpoint                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Breath Analysis (Tactical)                  │
│      Analyzes: volume, tempo, intensity, silence            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Coaching Intelligence (Tactical - Fast)           │
│  should_coach_speak() - Criticality-based decision          │
│  • critical = 5s interval                                   │
│  • moderate = 8-12s interval                                │
│  • calm = silence preferred                                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          Voice Intelligence (Tactical - Fast)               │
│  should_stay_silent() - Optimal breathing detection         │
│  • Good breathing = confidence = silence                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│     🧠 STRATEGIC BRAIN (Claude - Every 2-3 minutes)         │
│                                                             │
│  Triggered ONLY when:                                       │
│  • First call at 2 minutes                                  │
│  • Then every 3 minutes                                     │
│  • NOT on every breath                                      │
│                                                             │
│  Input (Structured Summary):                                │
│  {                                                          │
│    "phase": "intense",                                      │
│    "breath_trend": "erratic",                               │
│    "duration_struggling": 92,                               │
│    "recent_coaching": ["slow down", "control exhale"]      │
│  }                                                          │
│                                                             │
│  Output (Strategic Guidance):                               │
│  {                                                          │
│    "strategy": "reduce_overload",                           │
│    "tone": "calm_firm",                                     │
│    "message_goal": "restore_rhythm",                        │
│    "suggested_phrase": "Control the exhale."               │
│  }                                                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Message Selection (Priority Order)             │
│                                                             │
│  1. Strategic Brain phrase (if available this cycle)        │
│  2. Pattern insight phrase (hybrid mode)                    │
│  3. Config phrase (default, fast)                           │
│                                                             │
│  System decides: Strategic guidance OR config phrase        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                ElevenLabs TTS (1-2 seconds)                 │
│         Generates audio with cloned voice                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Audio Response                         │
│              Returns URL to generated audio                 │
└─────────────────────────────────────────────────────────────┘
```

## Summary

The Strategic Brain is an **assistant** to the coaching intelligence, not the boss. It provides strategic guidance every 2-3 minutes while the tactical system handles breath-by-breath decisions. This architecture ensures:

- ⚡ Fast tactical responses (immediate)
- 🧠 Strategic context (every 2-3 min)
- 💰 Cost-effective ($0.015 per workout)
- 🎯 High-quality coaching (Claude + rule-based)

Claude thinks slowly. Your system reacts fast. ElevenLabs speaks cleanly.

**You're building a coach, not a chatbot — and it shows.**
