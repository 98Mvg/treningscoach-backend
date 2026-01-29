# 🧠 Brain Adapters

This directory contains AI brain implementations that the Brain Router can use.

## Available Brains

- **config** - Simple config-based messages (no AI, no API key needed)
- **claude** - Claude AI by Anthropic
- **openai** - GPT models by OpenAI
- **nvidia** - Coming soon (PersonaPlex)

## How to Switch Brains

### Via Config File

Edit `backend/config.py`:

```python
ACTIVE_BRAIN = "claude"  # or "openai" or "config"
```

### Via API (at runtime)

```bash
curl -X POST http://localhost:5001/brain/switch \
  -H "Content-Type: application/json" \
  -d '{"brain": "claude"}'
```

### Check Current Brain

```bash
curl http://localhost:5001/brain/health
```

## Setting Up AI Brains

### Claude Brain

1. Get API key from https://console.anthropic.com
2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   ```
3. Install dependency: `pip install anthropic`
4. Set `ACTIVE_BRAIN = "claude"` in config.py

### OpenAI Brain

1. Get API key from https://platform.openai.com
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```
3. Install dependency: `pip install openai`
4. Set `ACTIVE_BRAIN = "openai"` in config.py

### Config Brain (Default)

No setup needed! Uses messages from `config.py` directly.

## Adding a New Brain

To add a new AI provider (e.g., Nvidia PersonaPlex):

1. Create `nvidia_brain.py` in this directory
2. Inherit from `BaseBrain`:

```python
from .base_brain import BaseBrain

class NvidiaBrain(BaseBrain):
    def __init__(self, api_key=None):
        super().__init__(api_key)
        # Initialize your API client

    def get_coaching_response(self, breath_data, phase="intense"):
        # Call your API and return coaching message
        pass

    def get_provider_name(self):
        return "nvidia"
```

3. Add to `__init__.py`:

```python
from .nvidia_brain import NvidiaBrain
__all__ = ['BaseBrain', 'ClaudeBrain', 'OpenAIBrain', 'NvidiaBrain']
```

4. Update `brain_router.py` to support the new brain:

```python
elif self.brain_type == "nvidia":
    from brains.nvidia_brain import NvidiaBrain
    self.brain = NvidiaBrain()
```

5. Update `config.py` to allow the new brain type

## Architecture

```
iOS App / Website
        ↓
   Brain Router (backend/brain_router.py)
        ↓
    ┌───┴────┬──────────┬──────────┐
    ↓        ↓          ↓          ↓
  Config   Claude    OpenAI    Nvidia
  Brain    Brain     Brain     Brain
```

The app NEVER knows which brain is active - it just talks to the Brain Router API.

## Benefits

- ✅ Swap AI providers instantly without changing app code
- ✅ A/B test different models
- ✅ Fallback to config if API fails
- ✅ Add new providers without touching existing code
- ✅ Hot-swap brains at runtime via API

## Files

- `base_brain.py` - Abstract interface all brains must implement
- `claude_brain.py` - Claude AI adapter
- `openai_brain.py` - OpenAI GPT adapter
- `__init__.py` - Package exports
