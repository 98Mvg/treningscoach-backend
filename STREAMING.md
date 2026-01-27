# 🌊 Streaming Chat Architecture

**Status:** Foundation complete, ready for session manager and endpoints

## What We Built

### ✅ Completed

1. **Streaming Brain Interface** (`brains/base_brain.py`)
   - Abstract interface with both legacy coaching + new streaming chat
   - Methods: `stream_chat()`, `chat()`, `supports_streaming()`

2. **Claude Streaming Brain** (`brains/claude_brain.py`)
   - Async streaming with `AsyncAnthropic`
   - Token-by-token responses via `stream.text_stream`
   - Backwards compatible with legacy coaching mode

3. **OpenAI Streaming Brain** (`brains/openai_brain.py`)
   - Async streaming with `AsyncOpenAI`
   - Token-by-token responses via delta chunks
   - Backwards compatible with legacy coaching mode

### 🔨 Next Steps

4. **Session Manager** - Store conversation history
5. **Streaming Endpoints** - SSE/WebSocket API
6. **Persona Manager** - Switchable system prompts
7. **iOS/Web Clients** - Consume streaming responses

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│              Client Layer                        │
│  ┌─────────────┐        ┌──────────────┐        │
│  │ iOS App     │        │  Web App     │        │
│  │ (Swift)     │        │  (React)     │        │
│  └──────┬──────┘        └──────┬───────┘        │
│         │ SSE/WebSocket        │                │
└─────────┼──────────────────────┼────────────────┘
          │                      │
          ▼                      ▼
┌──────────────────────────────────────────────────┐
│           Backend - Flask                        │
│                                                  │
│  📡 API Endpoints                                │
│  ├── POST /chat/start    (create session)       │
│  ├── POST /chat/stream   (SSE streaming)        │
│  └── POST /chat/message  (non-streaming)        │
│                                                  │
│  💾 Session Manager                              │
│  ├── Create/get sessions                        │
│  ├── Store message history                      │
│  └── Apply personas                             │
│                                                  │
│  🧠 Brain Router                                 │
│  └─┬─ Claude Brain  (streaming)                 │
│    ├─ OpenAI Brain  (streaming)                 │
│    └─ Config Brain  (mock)                      │
└──────────────────────────────────────────────────┘
```

---

## How Streaming Works

### 1. Client Starts Session

```http
POST /chat/start
{
  "user_id": "user123",
  "persona": "fitness_coach"
}

Response:
{
  "session_id": "session_user123_1234567890",
  "persona": "fitness_coach"
}
```

### 2. Client Sends Message (Streaming)

```http
POST /chat/stream
{
  "session_id": "session_...",
  "message": "How's it going?"
}

Response: (SSE stream)
data: {"token": "Going "}
data: {"token": "great! "}
data: {"token": "Ready "}
data: {"token": "to "}
data: {"token": "train?"}
data: {"done": true}
```

### 3. Backend Flow

```python
# 1. Get session history
messages = session_manager.get_messages(session_id)
# [{"role": "user", "content": "..."}, ...]

# 2. Get persona
persona = session_manager.get_persona(session_id)
system_prompt = PersonaManager.get_system_prompt(persona)

# 3. Stream from brain
async for token in brain.stream_chat(messages, system_prompt):
    yield f"data: {json.dumps({'token': token})}\n\n"

# 4. Save assistant response
session_manager.add_message(session_id, "assistant", full_response)
```

---

## Code Examples

### Claude Streaming (Already Implemented)

```python
from brains.claude_brain import ClaudeBrain

brain = ClaudeBrain()

messages = [
    {"role": "user", "content": "Hey! Ready to train?"}
]

system_prompt = "You are a motivating fitness coach."

# Stream response
async for token in brain.stream_chat(messages, system_prompt):
    print(token, end="", flush=True)

# Output (token by token):
# L e t ' s   G O !   P U S H   I T !
```

### OpenAI Streaming (Already Implemented)

```python
from brains.openai_brain import OpenAIBrain

brain = OpenAIBrain()

# Same interface as Claude!
async for token in brain.stream_chat(messages, system_prompt):
    print(token, end="", flush=True)
```

---

## Session Manager (To Implement)

```python
# backend/session_manager.py

class SessionManager:
    """Manages conversation sessions and history."""

    def __init__(self):
        # MVP: in-memory dict
        # Production: Redis or PostgreSQL
        self.sessions = {}

    def create_session(self, user_id: str, persona: str = "default") -> str:
        """Create new session, return session_id."""
        session_id = f"session_{user_id}_{timestamp}"
        self.sessions[session_id] = {
            "user_id": user_id,
            "persona": persona,
            "messages": [],
            "created_at": now,
        }
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        """Add message to history."""
        self.sessions[session_id]["messages"].append({
            "role": role,
            "content": content
        })

    def get_messages(self, session_id: str) -> List[Dict]:
        """Get conversation history."""
        return self.sessions[session_id]["messages"]

    def get_persona(self, session_id: str) -> str:
        """Get session persona."""
        return self.sessions[session_id]["persona"]
```

---

## Streaming Endpoint (To Implement)

```python
# backend/main.py

from flask import Flask, Response, stream_with_context
import asyncio

@app.route('/chat/stream', methods=['POST'])
def stream_chat():
    """Streaming chat endpoint (SSE)."""

    data = request.get_json()
    session_id = data['session_id']
    user_message = data['message']

    # Add user message
    session_manager.add_message(session_id, "user", user_message)

    # Get history and persona
    messages = session_manager.get_messages(session_id)
    persona = session_manager.get_persona(session_id)
    system_prompt = PersonaManager.get_system_prompt(persona)

    def generate():
        """SSE generator."""
        loop = asyncio.new_event_loop()
        full_response = ""

        async def stream():
            nonlocal full_response
            # Stream from brain
            async for token in brain_router.stream_chat(messages, system_prompt):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"

        # Run async stream
        for chunk in loop.run_until_complete(consume_async(stream())):
            yield chunk

        # Done signal
        yield f"data: {json.dumps({'done': True})}\n\n"

        # Save response
        session_manager.add_message(session_id, "assistant", full_response)
        loop.close()

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache'}
    )
```

---

## Persona System

```python
# backend/persona_manager.py

PERSONAS = {
    "fitness_coach": """You are a motivating fitness coach.
        - Short, powerful messages
        - Use CAPS for intensity
        - Adapt to user's breathing level""",

    "calm_coach": """You are a calm, soothing coach.
        - Speak gently and supportively
        - Focus on breath and mindfulness""",

    "drill_sergeant": """You are a tough drill sergeant coach.
        - Demanding and intense
        - Push hard but keep them safe
        - No excuses accepted""",

    "default": """You are a helpful AI assistant."""
}

def get_system_prompt(persona: str) -> str:
    return PERSONAS.get(persona, PERSONAS["default"])
```

---

## iOS Client Example

```swift
class StreamingChatService {
    func streamMessage(sessionId: String, message: String, onToken: @escaping (String) -> Void) {
        let url = URL(string: "\(baseURL)/chat/stream")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["session_id": sessionId, "message": message]
        request.httpBody = try? JSONEncoder().encode(body)

        URLSession.shared.dataTask(with: request) { data, _, _ in
            guard let data = data else { return }
            let lines = String(data: data, encoding: .utf8)?.components(separatedBy: "\n\n") ?? []

            for line in lines {
                if line.hasPrefix("data: ") {
                    let json = line.replacingOccurrences(of: "data: ", with: "")
                    if let data = json.data(using: .utf8),
                       let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let token = dict["token"] as? String {
                        DispatchQueue.main.async {
                            onToken(token)
                        }
                    }
                }
            }
        }.resume()
    }
}
```

---

## Web Client Example (React)

```javascript
async function streamChat(sessionId, message, onToken) {
  const response = await fetch('http://localhost:5001/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));
        if (data.token) {
          onToken(data.token);  // Update UI
        }
      }
    }
  }
}
```

---

## Benefits

✅ **Real-time experience** - Tokens arrive as they're generated
✅ **Same interface** - Claude and OpenAI work identically
✅ **Backwards compatible** - Legacy coaching mode still works
✅ **Session memory** - Full conversation history
✅ **Personas** - Switchable AI personalities
✅ **Future-proof** - Ready for Nvidia PersonaPlex

---

## Comparison: Legacy vs Streaming

| Feature | Legacy (Current) | Streaming (New) |
|---------|-----------------|-----------------|
| Response | Wait for full response | Tokens arrive immediately |
| UX | Loading spinner | Typewriter effect |
| API | `/coach` (breath analysis) | `/chat/stream` (conversation) |
| Memory | Stateless | Session-based history |
| Personas | Fixed coaching style | Switchable personalities |
| Streaming | ❌ No | ✅ Yes |

---

## Next Implementation Steps

### 1. Create Session Manager

```bash
# Create session_manager.py with:
- create_session()
- add_message()
- get_messages()
- get_persona()
```

### 2. Create Persona Manager

```bash
# Create persona_manager.py with:
- PERSONAS dict
- get_system_prompt()
- list_personas()
```

### 3. Add Streaming Endpoints

```bash
# Update main.py with:
- POST /chat/start
- POST /chat/stream (SSE)
- POST /chat/message (non-streaming)
```

### 4. Update Requirements

```bash
# Already has:
anthropic>=0.40.0  # AsyncAnthropic
openai>=1.0.0      # AsyncOpenAI

# May need:
aiohttp  # For async HTTP if using Nvidia later
```

### 5. Test Locally

```bash
cd backend
python3 -c "
import asyncio
from brains.claude_brain import ClaudeBrain

async def test():
    brain = ClaudeBrain()
    messages = [{'role': 'user', 'content': 'Ready to train?'}]
    async for token in brain.stream_chat(messages, 'You are a motivating coach'):
        print(token, end='', flush=True)

asyncio.run(test())
"
```

---

## Current Status

**Foundation: ✅ Complete**
- Base brain interface supports streaming
- Claude brain streams via AsyncAnthropic
- OpenAI brain streams via AsyncOpenAI
- Both maintain legacy coaching compatibility

**Next: Build Session + Endpoints**
- Session manager for conversation memory
- Streaming SSE endpoints
- Persona system
- Client examples

Your architecture is now ready for real-time conversational AI with any provider! 🚀

---

## Questions?

**Q: Do I need to change the iOS app?**
A: No for legacy coaching mode. Yes for new streaming chat mode (new endpoints).

**Q: Can I use this with the current `/coach` endpoint?**
A: Yes! Legacy coaching mode still works exactly as before.

**Q: How do I test streaming without building endpoints?**
A: Use the Python async test above - calls brain directly.

**Q: When can I add Nvidia?**
A: Anytime! Just create `nvidia_brain.py` with `stream_chat()` method.

**Q: Does this cost more?**
A: Same cost per token. Streaming just delivers tokens faster, doesn't generate more.
