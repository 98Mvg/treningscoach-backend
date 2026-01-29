"""
ElevenLabs TTS Integration for Treningscoach
Fast, cloud-based voice cloning with your custom voice
"""

import os
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import logging

logger = logging.getLogger(__name__)

class ElevenLabsTTS:
    def __init__(self, api_key: str, voice_id: str):
        """
        Initialize ElevenLabs TTS client
        
        Args:
            api_key: Your ElevenLabs API key (from dashboard)
            voice_id: Your cloned voice ID
        """
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        
        # Cache directory for generated audio
        self.cache_dir = os.path.join(os.path.dirname(__file__), "output", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"✅ ElevenLabs initialized with voice ID: {voice_id[:8]}...")
    
    def generate_audio(self, text: str, output_path: str = None) -> str:
        """
        Generate speech from text using your cloned voice
        
        Args:
            text: The text to synthesize
            output_path: Where to save the audio file
            
        Returns:
            Path to the generated audio file
        """
        if not output_path:
            import time
            output_path = os.path.join(
                self.cache_dir,
                f"coach_{int(time.time() * 1000)}.mp3"
            )
        
        logger.info(f"🎙️ Generating with ElevenLabs: '{text}'")
        
        # Generate audio using text_to_speech method
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id="eleven_multilingual_v2",  # Supports Norwegian + English
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )

        # Save to file
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        logger.info(f"✅ Audio saved: {output_path}")
        return output_path


# Example usage
if __name__ == "__main__":
    # Test the integration
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    
    if not api_key or not voice_id:
        print("⚠️  Set environment variables:")
        print("   export ELEVENLABS_API_KEY='your_key'")
        print("   export ELEVENLABS_VOICE_ID='your_voice_id'")
    else:
        tts = ElevenLabsTTS(api_key, voice_id)
        audio_file = tts.generate_audio("Perfect! Keep going!")
        print(f"✅ Generated: {audio_file}")
