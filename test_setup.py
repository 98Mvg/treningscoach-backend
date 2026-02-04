#!/usr/bin/env python3
"""
test_setup.py - Verify Qwen3-TTS integration setup

Run this before starting the server to check everything is configured correctly.
"""

import os
import sys

def check_env_file():
    """Check if .env file exists and has required keys."""
    print("📋 Checking .env configuration...")

    if not os.path.exists('.env'):
        print("  ❌ .env file not found")
        print("     Run: cp .env.example .env")
        return False

    with open('.env', 'r') as f:
        env_content = f.read()

    if 'ANTHROPIC_API_KEY' not in env_content:
        print("  ❌ ANTHROPIC_API_KEY not found in .env")
        return False

    if 'sk-ant-your_api_key_here' in env_content:
        print("  ⚠️  .env still has placeholder API key")
        print("     Get your key from: https://console.anthropic.com/")
        return False

    print("  ✅ .env configured")
    return True


def check_reference_audio():
    """Check if reference audio exists and has correct format."""
    print("\n🎤 Checking reference audio...")

    audio_path = "voices/coach_voice.wav"

    if not os.path.exists(audio_path):
        print(f"  ❌ Reference audio not found: {audio_path}")
        print("     Run: mkdir -p voices && cp reference_audio/coach_voice.wav voices/")
        return False

    file_size = os.path.getsize(audio_path)
    file_size_kb = file_size / 1024

    print(f"  ✅ Reference audio found: {file_size_kb:.1f} KB")

    # Check if it's a valid WAV file
    try:
        import soundfile as sf
        audio, sr = sf.read(audio_path)
        duration = len(audio) / sr
        print(f"  ✅ Duration: {duration:.1f} seconds, Sample rate: {sr} Hz")

        if duration < 10:
            print("  ⚠️  Audio is shorter than recommended (10-30 seconds)")
        elif duration > 30:
            print("  ⚠️  Audio is longer than recommended (10-30 seconds)")

    except ImportError:
        print("  ⚠️  soundfile not installed, cannot verify audio format")
    except Exception as e:
        print(f"  ❌ Error reading audio: {e}")
        return False

    return True


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n📦 Checking dependencies...")

    required = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'anthropic': 'Anthropic (Claude API)',
        'torch': 'PyTorch',
        'soundfile': 'soundfile',
        'qwen_tts': 'Qwen3-TTS'
    }

    all_installed = True

    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} not installed")
            all_installed = False

    if not all_installed:
        print("\n  Run: pip install -r requirements.txt")

    return all_installed


def check_cuda():
    """Check CUDA availability for GPU acceleration."""
    print("\n🎮 Checking GPU/CUDA...")

    try:
        import torch

        if torch.cuda.is_available():
            print(f"  ✅ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"     PyTorch will use GPU for faster TTS")
        else:
            print("  ℹ️  CUDA not available, will use CPU")
            print("     TTS will work but be slower (~3-5s vs ~1-2s)")

    except ImportError:
        print("  ⚠️  PyTorch not installed, cannot check CUDA")

    return True


def test_claude_api():
    """Test Claude API connection (optional - requires API key)."""
    print("\n🤖 Testing Claude API...")

    try:
        from anthropic import Anthropic
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key or api_key.startswith("sk-ant-your"):
            print("  ⚠️  Skipping API test (placeholder key)")
            return True

        client = Anthropic(api_key=api_key)

        # Simple test message
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'OK'"}]
        )

        if response.content[0].text:
            print("  ✅ Claude API connection successful")
            return True
        else:
            print("  ❌ Claude API returned empty response")
            return False

    except ImportError:
        print("  ⚠️  anthropic package not installed")
        return False
    except Exception as e:
        print(f"  ❌ Claude API error: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("🎯 Treningscoach Setup Verification")
    print("=" * 60)

    checks = [
        check_env_file(),
        check_reference_audio(),
        check_dependencies(),
        check_cuda(),
        test_claude_api()
    ]

    print("\n" + "=" * 60)

    if all(checks):
        print("✅ All checks passed! Ready to start server.")
        print("\nRun: ./start.sh")
        print("Or:  uvicorn server:app --host 0.0.0.0 --port 8000 --reload")
        return 0
    else:
        print("⚠️  Some checks failed. Fix issues above before starting server.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
