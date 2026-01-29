# 🧠 Brain Router Architecture

The Brain Router is the abstraction layer that lets you swap AI providers without changing your app code.

## Architecture

```
┌─────────────────┐
│  iOS App        │
│  Website        │
└────────┬────────┘
         │
         │ HTTP API
         │
┌────────▼────────┐
│  Brain Router   │  ← Single entry point
│  (main.py)      │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬─────────┐
    │         │         │         │
┌───▼───┐ ┌──▼───┐ ┌───▼────┐ ┌──▼─────┐
│Config │ │Claude│ │OpenAI  │ │Nvidia  │
│Brain  │ │Brain │ │Brain   │ │(soon)  │
└───────┘ └──────┘ └────────┘ └────────┘
```

## Key Benefits

✅ **Swap AI providers instantly** - Change `ACTIVE_BRAIN` in config, no app changes needed
✅ **A/B test models** - Compare Claude vs OpenAI responses
✅ **Automatic fallback** - If AI fails, falls back to config messages
✅ **Add providers easily** - Plug in new AI without touching existing code
✅ **Runtime switching** - Change brains via API without restarting

## Quick Start

### 1. Choose Your Brain

Edit `backend/config.py`:

```python
ACTIVE_BRAIN = "config"  # Options: "config", "claude", "openai"
```

### 2. Setup (if using AI)

For Claude:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
pip install anthropic
```

For OpenAI:
```bash
export OPENAI_API_KEY="sk-proj-..."
pip install openai
```

### 3. Start Backend

```bash
cd backend
python3 main.py
```

You'll see:
```
✅ Brain Router: Using config-based messages (no AI)
```

## API Endpoints

### Check Brain Health

```bash
curl http://localhost:5001/brain/health
```

Response:
```json
{
  "active_brain": "config",
  "healthy": true,
  "message": "OK"
}
```

### Switch Brain (Runtime)

```bash
curl -X POST http://localhost:5001/brain/switch \
  -H "Content-Type: application/json" \
  -d '{"brain": "claude"}'
```

Response:
```json
{
  "success": true,
  "active_brain": "claude",
  "message": "Switched to claude"
}
```

### Coach Endpoint (Uses Active Brain)

```bash
curl -X POST http://localhost:5001/coach \
  -F "audio=@breath.wav" \
  -F "phase=intense"
```

Response:
```json
{
  "text": "PUSH! Hardere!",
  "breath_analysis": {...},
  "audio_url": "/download/coach_xxx.mp3"
}
```

## Available Brains

### Config Brain (Default)

- **No AI, no API key needed**
- Uses messages from `config.py`
- Fast and free
- Perfect for development and testing

```python
COACH_MESSAGES = {
    "intense": {
        "rolig": ["PUSH! Hardere!", "Du klarer mer!"],
        "moderat": ["Fortsett! Du har mer!"],
        "hard": ["Ja! Hold ut! Ti til!"]
    }
}
```

### Claude Brain

- **Claude 3.5 Sonnet by Anthropic**
- Dynamic, context-aware responses
- Uses config messages as style guide
- Requires `ANTHROPIC_API_KEY`

Example response: "PUSH MER! 15 SEKUNDER!"

### OpenAI Brain

- **GPT-4o by OpenAI**
- Dynamic, context-aware responses
- Uses config messages as style guide
- Requires `OPENAI_API_KEY`

Example response: "FORTSETT! DU HAR DET!"

## How It Works

### 1. App Makes Request

```swift
// iOS app doesn't know which brain is active
apiService.sendBreath(audio: audioData, phase: "intense")
```

### 2. Brain Router Receives

```python
# backend/main.py
@app.route('/coach', methods=['POST'])
def coach():
    breath_data = analyze_breath(audio_file)
    response = brain_router.get_coaching_response(breath_data, phase)
    return jsonify({"text": response})
```

### 3. Brain Router Delegates

```python
# backend/brain_router.py
def get_coaching_response(breath_data, phase):
    if self.brain is not None:
        return self.brain.get_coaching_response(breath_data, phase)
    return self._get_config_response(breath_data, phase)
```

### 4. Active Brain Responds

```python
# backend/brains/claude_brain.py
def get_coaching_response(breath_data, phase):
    # Call Claude API with breath analysis context
    message = self.client.messages.create(...)
    return message.content[0].text
```

## Adding a New Brain

Want to add Nvidia PersonaPlex or another provider?

### 1. Create Brain File

`backend/brains/nvidia_brain.py`:

```python
from .base_brain import BaseBrain
import os
from nvidia_api import NvidiaClient  # Your API client

class NvidiaBrain(BaseBrain):
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.client = NvidiaClient(api_key=self.api_key)

    def get_coaching_response(self, breath_data, phase="intense"):
        intensitet = breath_data.get("intensitet", "moderat")

        # Critical override
        if intensitet == "kritisk":
            return random.choice(config.COACH_MESSAGES["kritisk"])

        # Build prompt with breath context
        prompt = f"Breathe intensity: {intensitet}, phase: {phase}"

        # Call your API
        response = self.client.generate(prompt)
        return response.text

    def get_provider_name(self):
        return "nvidia"
```

### 2. Register Brain

`backend/brains/__init__.py`:

```python
from .nvidia_brain import NvidiaBrain
__all__ = ['BaseBrain', 'ClaudeBrain', 'OpenAIBrain', 'NvidiaBrain']
```

### 3. Add to Router

`backend/brain_router.py`:

```python
elif self.brain_type == "nvidia":
    from brains.nvidia_brain import NvidiaBrain
    self.brain = NvidiaBrain()
    print(f"✅ Brain Router: Using Nvidia")
```

### 4. Update Config

`backend/config.py`:

```python
ACTIVE_BRAIN = "nvidia"  # Add as option
```

### 5. Done!

```bash
export NVIDIA_API_KEY="your-key"
python3 main.py
```

Your app now uses Nvidia without any iOS code changes!

## Best Practices

### Development

Use `config` brain for fast local development:

```python
ACTIVE_BRAIN = "config"
```

### Testing Different Models

Use runtime switching to A/B test:

```bash
# Test with Claude
curl -X POST localhost:5001/brain/switch -d '{"brain":"claude"}'

# Test with OpenAI
curl -X POST localhost:5001/brain/switch -d '{"brain":"openai"}'
```

### Production

Set via environment variable:

```bash
export ACTIVE_BRAIN="claude"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Fallback Strategy

AI brains automatically fall back to config messages if API fails:

```python
try:
    return self.brain.get_coaching_response(breath_data, phase)
except Exception as e:
    logger.error(f"Brain error: {e}")
    return self._get_config_response(breath_data, phase)
```

## Cost Comparison

| Brain | Cost | Latency | Quality |
|-------|------|---------|---------|
| Config | Free | 1ms | Static |
| Claude | ~$0.003/msg | 500ms | Dynamic |
| OpenAI | ~$0.002/msg | 400ms | Dynamic |

## Files

```
backend/
├── brain_router.py          # Main router
├── config.py                # Brain selection
├── main.py                  # API endpoints
└── brains/
    ├── __init__.py
    ├── base_brain.py        # Abstract interface
    ├── claude_brain.py      # Claude adapter
    ├── openai_brain.py      # OpenAI adapter
    └── README.md            # Detailed brain docs
```

## Deployment

### Render (Production)

Add environment variables in Render dashboard:

```
ACTIVE_BRAIN=claude
ANTHROPIC_API_KEY=sk-ant-xxx
```

Deploy:

```bash
git add .
git commit -m "Add Brain Router"
git push
```

Render auto-deploys in 2-3 minutes.

### Local Testing

```bash
cd backend
export ACTIVE_BRAIN=claude
export ANTHROPIC_API_KEY=sk-ant-xxx
python3 main.py
```

## Troubleshooting

### Brain fails to initialize

```
⚠️ Brain Router: Failed to initialize Claude: ...
⚠️ Brain Router: Falling back to config-based messages
```

**Solution**: Check API key is set correctly

```bash
echo $ANTHROPIC_API_KEY
```

### Health check fails

```json
{"healthy": false, "message": "Brain health check failed"}
```

**Solution**: Test API key manually or switch to config brain

### Import errors

```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution**: Install dependencies

```bash
pip install -r requirements.txt
```

## Summary

The Brain Router gives you:

1. **Single API** - App talks to one endpoint
2. **Multiple brains** - Swap providers anytime
3. **Easy extension** - Add new providers in minutes
4. **Zero app changes** - iOS/web code never changes
5. **Production ready** - Fallbacks, health checks, runtime switching

Your app is now future-proof for any AI provider!

---

**See also:**
- [backend/brains/README.md](backend/brains/README.md) - Detailed brain implementation guide
- [CUSTOMIZATION.md](CUSTOMIZATION.md) - Customize messages and behavior
- [QUICK_START.md](QUICK_START.md) - Get started in 5 minutes
