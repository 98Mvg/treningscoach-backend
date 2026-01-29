# Strategic Brain Setup Guide

## Quick Start

### 1. Get Anthropic API Key

1. Go to: https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-...`)

### 2. Add to .env File

```bash
cd backend
nano .env
```

Add this line:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Save and exit (Ctrl+O, Enter, Ctrl+X)

### 3. Test Strategic Brain

```bash
cd backend
python3 strategic_brain.py
```

You should see:
```
✅ Strategic Brain is available
Strategic insight: Tempo is settling. Good.
```

### 4. Start Backend with Strategic Brain

```bash
cd backend
python3 main.py
```

Look for these log messages:
```
✅ Strategic Brain initialized with Claude
✅ Strategic Brain (Claude) is available
```

### 5. Test with iOS App

1. Start a workout in the iOS app
2. Wait 2 minutes
3. Check backend logs for:
```
🧠 Requesting strategic guidance from Claude...
✅ Strategic guidance: {'strategy': 'maintain_pace', ...}
🧠 Using Strategic Brain phrase: Tempo is settling. Good.
```

## Troubleshooting

### Strategic Brain Not Available

**Problem:**
```
⚠️ Strategic Brain disabled (no ANTHROPIC_API_KEY)
```

**Solution:**
1. Check .env file exists: `ls -la backend/.env`
2. Check ANTHROPIC_API_KEY is set: `cat backend/.env | grep ANTHROPIC`
3. Restart backend: `pkill -f "python.*main.py" && cd backend && python3 main.py`

### API Key Invalid

**Problem:**
```
Strategic Brain error: authentication error
```

**Solution:**
1. Verify your API key at: https://console.anthropic.com/settings/keys
2. Make sure you copied the full key (starts with `sk-ant-`)
3. Update .env file with correct key
4. Restart backend

### No Strategic Insights

**Problem:**
Strategic Brain initialized but no insights appear in logs.

**Reason:**
Strategic Brain only triggers:
- At 2 minutes into workout (first insight)
- Every 3 minutes after that

**Solution:**
1. Make sure workout is running for at least 2 minutes
2. Check `elapsed_seconds` in logs
3. Look for: `🧠 Requesting strategic guidance from Claude...`

### Strategic Insights Too Frequent

**Problem:**
Claude API costs are too high.

**Solution:**
Edit `strategic_brain.py` timing:

```python
# Change these values (in seconds)
if elapsed_seconds >= 180:  # First at 3 minutes (was 120)
    return True

if time_since_last >= 300:  # Every 5 minutes (was 180)
    return True
```

## Configuration Options

### Timing (strategic_brain.py)

```python
# First strategic insight
elapsed_seconds >= 120  # 2 minutes (default)

# Subsequent insights
time_since_last >= 180  # 3 minutes (default)
```

Recommended settings:
- **Aggressive coaching**: 120s first, 180s interval
- **Balanced coaching**: 180s first, 240s interval
- **Minimal coaching**: 240s first, 300s interval

### Model Settings (strategic_brain.py)

```python
model="claude-3-5-sonnet-20241022",  # Best quality
max_tokens=200,  # Strategic guidance length
temperature=0.7,  # Creativity level (0.0-1.0)
```

Trade-offs:
- **claude-3-5-sonnet**: Best quality, $3/M tokens
- **claude-3-haiku**: Faster, cheaper, good quality, $0.25/M tokens

To use Haiku:
```python
model="claude-3-haiku-20240307",
```

### Cost Optimization

**Current Cost (Sonnet):**
- Per strategic insight: ~$0.001
- Per 45-min workout (15 insights): ~$0.015
- Per 100 workouts: ~$1.50

**With Haiku:**
- Per strategic insight: ~$0.0001
- Per 45-min workout: ~$0.0015
- Per 100 workouts: ~$0.15

**To minimize costs:**
1. Increase insight interval (3 min → 5 min)
2. Use Haiku model instead of Sonnet
3. Set ANTHROPIC_API_KEY="" to disable

## Monitoring

### View Strategic Insights in Real-time

```bash
cd backend
tail -f logs/backend.log | grep "🧠"
```

You'll see:
```
🧠 Requesting strategic guidance from Claude...
✅ Strategic guidance: {'strategy': 'reduce_overload', 'tone': 'calm_firm', ...}
🧠 Using Strategic Brain phrase: Control the exhale. Let the breath settle.
```

### Check Strategic Brain Status

```bash
cd backend
python3 -c "from strategic_brain import get_strategic_brain; brain = get_strategic_brain(); print('Available:', brain.is_available())"
```

## Advanced Usage

### Custom Strategic Prompts

Edit `strategic_brain.py`:

```python
def _build_strategic_prompt(self, ...):
    # Add your custom context
    prompt = f"""Session summary for strategic guidance:

Phase: {phase}
Elapsed: {minutes} minutes
...

YOUR CUSTOM CONTEXT HERE

Provide strategic guidance for this moment.
"""
```

### Custom Response Format

Edit `strategic_brain.py`:

```python
def _parse_strategic_response(self, response: str) -> Dict:
    # Add your custom parsing logic
    guidance = {
        "strategy": "your_strategy",
        "tone": "your_tone",
        "message_goal": "your_goal",
        "suggested_phrase": "your_phrase"
    }
    return guidance
```

### Session Summaries

End-of-workout reflection:

```python
summary = strategic_brain.session_summary(
    breath_history=all_breaths,
    coaching_history=all_messages,
    total_time=workout_duration,
    phase=final_phase
)
```

Returns: "Good session. Tempo control improved."

## FAQ

**Q: Does Strategic Brain slow down the app?**
A: No. It runs asynchronously every 2-3 minutes. Tactical decisions are still instant.

**Q: What if ANTHROPIC_API_KEY is not set?**
A: Strategic Brain disables gracefully. The app works normally with config phrases.

**Q: Can I use both Strategic Brain and pattern insights?**
A: Yes! Priority: Strategic Brain > Pattern insights > Config phrases

**Q: How much does it cost?**
A: ~$0.015 per 45-min workout with Sonnet, ~$0.0015 with Haiku.

**Q: Does it work offline?**
A: No. Strategic Brain requires API access. Use config phrases for offline mode.

**Q: Can I customize the coaching style?**
A: Yes! Edit the system prompt in `strategic_brain.py`:

```python
def _get_system_prompt(self) -> str:
    return """Your custom coaching personality here..."""
```

## Production Checklist

Before deploying Strategic Brain to production:

- [ ] ANTHROPIC_API_KEY set in production .env
- [ ] Test Strategic Brain with `python3 strategic_brain.py`
- [ ] Verify logs show "✅ Strategic Brain (Claude) is available"
- [ ] Monitor first strategic insight at 2 minutes
- [ ] Check API costs after 10 test workouts
- [ ] Set up API usage alerts in Anthropic console
- [ ] Configure timing based on coaching frequency preference
- [ ] Test graceful degradation (disable API key and verify app still works)

## Support

If you encounter issues:

1. Check logs: `tail -f logs/backend.log`
2. Test standalone: `python3 strategic_brain.py`
3. Verify API key: https://console.anthropic.com/settings/keys
4. Check .env file: `cat backend/.env`
5. Restart backend: `pkill -f "python.*main.py" && python3 main.py`

Strategic Brain is optional. If it's not working, the app continues with tactical intelligence and config phrases.
