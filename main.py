# main.py - HOVEDFIL FOR TRENINGSCOACH BACKEND

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import json
import wave
import math
import random
import logging
from datetime import datetime
import config  # Import central configuration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for iOS app

# Configuration from config.py
MAX_FILE_SIZE = config.MAX_FILE_SIZE
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

# Mapper for å lagre filer midlertidig
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ============================================
# HELPER FUNCTIONS
# ============================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# PUSTE-ANALYSE (ENKEL VERSJON)
# ============================================

def analyze_breath(audio_file_path):
    """
    Analyserer lydopptak og returnerer puste-intensitet

    Returnerer:
    - stillhet: Hvor mye stille pause det er (0-100%)
    - volum: Hvor høyt pusten er (0-100)
    - tempo: Hvor raskt pusten kommer (pust per minutt)
    - intensitet: "rolig", "moderat", "hard", eller "kritisk"
    """

    try:
        # Åpner lydfilen
        with wave.open(audio_file_path, 'rb') as wav_file:
            # Henter ut informasjon
            frames = wav_file.readframes(wav_file.getnframes())
            sample_rate = wav_file.getframerate()
            num_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            duration = wav_file.getnframes() / float(sample_rate)

            # Beregn gjennomsnittlig volum (forenklet)
            # Vi konverterer bytes til tall og finner gjennomsnitt
            samples = []
            for i in range(0, len(frames), sample_width * num_channels):
                if i + sample_width <= len(frames):
                    # Les sample (forenklet - tar bare første kanal)
                    sample = int.from_bytes(
                        frames[i:i+sample_width],
                        byteorder='little',
                        signed=True
                    )
                    samples.append(abs(sample))

            if not samples:
                return default_analysis()

            # Beregn gjennomsnittlig volum (normalisert 0-100)
            avg_volume = sum(samples) / len(samples)
            max_possible = (2 ** (sample_width * 8 - 1)) - 1
            volume_percent = min(100, (avg_volume / max_possible) * 100 * 10)  # Forsterket

            # Estimér stillhet basert på hvor mange samples er under en terskel
            silence_threshold = max_possible * 0.01  # 1% av max
            silent_samples = sum(1 for s in samples if s < silence_threshold)
            silence_percent = (silent_samples / len(samples)) * 100

            # Estimér tempo (forenklet - basert på variasjon i volum)
            # Flere volum-endringer = raskere pust
            changes = 0
            threshold = max_possible * 0.05
            for i in range(1, len(samples)):
                if abs(samples[i] - samples[i-1]) > threshold:
                    changes += 1

            # Konverter til "pust per minutt" (estimat)
            tempo = min(60, (changes / duration) * 60 / 10)  # Justert

            # Bestem intensitet
            if volume_percent < 20 and silence_percent > 50:
                intensitet = "rolig"
            elif volume_percent < 40 and tempo < 20:
                intensitet = "moderat"
            elif volume_percent < 70 and tempo < 35:
                intensitet = "hard"
            else:
                intensitet = "kritisk"

            return {
                "stillhet": round(silence_percent, 1),
                "volum": round(volume_percent, 1),
                "tempo": round(tempo, 1),
                "intensitet": intensitet,
                "varighet": round(duration, 2)
            }

    except Exception as e:
        logger.error(f"Feil ved analyse: {e}", exc_info=True)
        return default_analysis()

def default_analysis():
    """Returner standard-analyse hvis noe går galt"""
    return {
        "stillhet": 50.0,
        "volum": 30.0,
        "tempo": 15.0,
        "intensitet": "moderat",
        "varighet": 2.0
    }

# ============================================
# COACH-LOGIKK
# ============================================

def get_coach_response(breath_data, phase="intense"):
    """
    Velger hva coachen skal si basert på pust-data

    Args:
        breath_data: Dictionary med stillhet, volum, tempo, intensitet
        phase: "warmup", "intense", eller "cooldown"

    Returns:
        Tekst som coachen skal si
    """

    intensitet = breath_data["intensitet"]

    # SIKKERHETSSJEKK FØRST
    if intensitet == "kritisk":
        return random.choice(config.COACH_MESSAGES["kritisk"])

    # OPPVARMING
    if phase == "warmup":
        return random.choice(config.COACH_MESSAGES["warmup"])

    # NEDKJØLING
    if phase == "cooldown":
        return random.choice(config.COACH_MESSAGES["cooldown"])

    # HARD TRENING
    if intensitet in config.COACH_MESSAGES["intense"]:
        return random.choice(config.COACH_MESSAGES["intense"][intensitet])

    return "Fortsett!"

# ============================================
# MOCK VOICE GENERATION (til du kobler PersonaPlex)
# ============================================

def generate_voice_mock(text):
    """
    Lager en "fake" lydfil mens vi venter på PersonaPlex
    I virkeligheten vil denne sende til PersonaPlex API

    For nå: kopierer en eksisterende lydfil eller lager stille
    """
    output_path = os.path.join(OUTPUT_FOLDER, f"coach_{datetime.now().timestamp()}.mp3")

    # TODO: Senere skal dette være:
    # response = personaplex_api.generate_speech(text)
    # save_audio(response, output_path)

    # For nå: Lag en placeholder-fil
    # Du kan legge inn noen ferdiginnspilte coach-lydklipp her
    with open(output_path, 'wb') as f:
        f.write(b'')  # Tom fil (placeholder)

    return output_path

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def home():
    """Hjemmeside - minimal ChatGPT-lik stemme-UI"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Treningscoach</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                height: 100vh;
                display: flex;
                flex-direction: column;
                background: linear-gradient(to bottom, #ffffff, #f5f5f7);
                overflow: hidden;
            }

            /* Header - diskré */
            .header {
                padding: 16px 20px;
                text-align: center;
            }

            .title {
                font-size: 18px;
                font-weight: 600;
                color: #1d1d1f;
                margin-bottom: 4px;
            }

            .status {
                font-size: 13px;
                color: #86868b;
                font-weight: 400;
            }

            /* Midten - tom og pustende */
            .center {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            /* Voice Orb - hovedfokus */
            .orb-container {
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
                padding-bottom: 60px;
            }

            .voice-orb {
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 8px 32px rgba(0, 122, 255, 0.3);
                position: relative;
            }

            .voice-orb:hover {
                transform: scale(1.05);
                box-shadow: 0 12px 40px rgba(0, 122, 255, 0.4);
            }

            .voice-orb.listening {
                animation: pulse 1.5s ease-in-out infinite;
                background: linear-gradient(135deg, #34C759 0%, #248A3D 100%);
                box-shadow: 0 8px 32px rgba(52, 199, 89, 0.4);
            }

            .voice-orb.speaking {
                animation: wave 1s ease-in-out infinite;
                background: linear-gradient(135deg, #FF3B30 0%, #C72C23 100%);
                box-shadow: 0 8px 32px rgba(255, 59, 48, 0.4);
            }

            @keyframes pulse {
                0%, 100% {
                    transform: scale(1);
                    opacity: 1;
                }
                50% {
                    transform: scale(1.1);
                    opacity: 0.9;
                }
            }

            @keyframes wave {
                0%, 100% {
                    transform: scale(1);
                }
                33% {
                    transform: scale(1.05);
                }
                66% {
                    transform: scale(0.95);
                }
            }

            .mic-icon {
                width: 48px;
                height: 48px;
                color: white;
            }

            /* Info text - subtil */
            .info {
                position: absolute;
                bottom: -40px;
                text-align: center;
                width: 100%;
                font-size: 14px;
                color: #86868b;
                opacity: 0.8;
            }

            /* Dokumentasjon - nederst */
            .footer {
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #86868b;
            }

            .footer a {
                color: #007AFF;
                text-decoration: none;
            }

            .footer a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <!-- Header -->
        <div class="header">
            <div class="title">Treningscoach</div>
            <div class="status" id="statusText">Ready</div>
        </div>

        <!-- Center - Voice Orb -->
        <div class="center">
            <div class="orb-container">
                <div class="voice-orb" id="voiceOrb" onclick="toggleVoice()">
                    <svg class="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                        <line x1="8" y1="23" x2="16" y2="23"></line>
                    </svg>
                </div>
                <div class="info" id="infoText">Click to start</div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <a href="/health">API Status</a> •
            <a href="https://github.com/98Mvg/treningscoach-backend">Documentation</a>
        </div>

        <script>
            let state = 'idle'; // idle, listening, speaking

            function toggleVoice() {
                const orb = document.getElementById('voiceOrb');
                const status = document.getElementById('statusText');
                const info = document.getElementById('infoText');

                if (state === 'idle') {
                    state = 'listening';
                    orb.classList.add('listening');
                    status.textContent = 'Listening';
                    info.textContent = 'Analyzing your breath...';

                    // Simulate analysis -> speaking
                    setTimeout(() => {
                        state = 'speaking';
                        orb.classList.remove('listening');
                        orb.classList.add('speaking');
                        status.textContent = 'Speaking';
                        info.textContent = 'Coach is responding...';

                        // Return to idle
                        setTimeout(() => {
                            state = 'idle';
                            orb.classList.remove('speaking');
                            status.textContent = 'Ready';
                            info.textContent = 'Click to start';
                        }, 3000);
                    }, 2000);
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Enkel helse-sjekk for å se at serveren lever"""
    return jsonify({
        "status": "healthy",
        "version": "1.1.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "analyze": "/analyze",
            "coach": "/coach",
            "download": "/download/<filename>"
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Mottar lydopptak fra app og analyserer pusten

    App sender: MP3/WAV fil
    Backend returnerer: JSON med puste-data
    """
    try:
        if 'audio' not in request.files:
            logger.warning("Analyze request missing audio file")
            return jsonify({"error": "Ingen lydfil mottatt"}), 400

        audio_file = request.files['audio']

        if audio_file.filename == '':
            return jsonify({"error": "Tom filnavn"}), 400

        # Validate file size
        audio_file.seek(0, os.SEEK_END)
        file_size = audio_file.tell()
        audio_file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": f"Fil for stor. Maks størrelse: {MAX_FILE_SIZE / 1024 / 1024}MB"}), 400

        # Lagre filen midlertidig
        filename = f"breath_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(filepath)

        logger.info(f"Analyzing audio file: {filename} ({file_size} bytes)")

        # Analyser pusten
        breath_data = analyze_breath(filepath)

        # Slett midlertidig fil
        try:
            os.remove(filepath)
        except Exception as e:
            logger.warning(f"Could not remove temp file {filepath}: {e}")

        logger.info(f"Analysis complete: {breath_data['intensitet']}")
        return jsonify(breath_data)

    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        return jsonify({"error": "Intern serverfeil"}), 500

@app.route('/coach', methods=['POST'])
def coach():
    """
    Hovedendepunkt: Mottar lyd, analyserer, returnerer coach-voice

    App sender:
    - audio: Lydfil
    - phase: "warmup", "intense", eller "cooldown"

    Backend returnerer:
    - Coach voice som MP3
    """
    try:
        if 'audio' not in request.files:
            logger.warning("Coach request missing audio file")
            return jsonify({"error": "Ingen lydfil mottatt"}), 400

        audio_file = request.files['audio']
        phase = request.form.get('phase', 'intense')

        if audio_file.filename == '':
            return jsonify({"error": "Tom filnavn"}), 400

        # Validate phase
        valid_phases = ['warmup', 'intense', 'cooldown']
        if phase not in valid_phases:
            return jsonify({"error": f"Ugyldig phase. Må være en av: {', '.join(valid_phases)}"}), 400

        # Validate file size
        audio_file.seek(0, os.SEEK_END)
        file_size = audio_file.tell()
        audio_file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": f"Fil for stor. Maks størrelse: {MAX_FILE_SIZE / 1024 / 1024}MB"}), 400

        # Lagre filen midlertidig
        filename = f"breath_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(filepath)

        logger.info(f"Coach request: {filename} ({file_size} bytes), phase={phase}")

        # Analyser pusten
        breath_data = analyze_breath(filepath)

        # Få coach-respons (tekst)
        coach_text = get_coach_response(breath_data, phase)

        # Generer voice (mock for nå)
        voice_file = generate_voice_mock(coach_text)

        # Slett midlertidig inndata-fil
        try:
            os.remove(filepath)
        except Exception as e:
            logger.warning(f"Could not remove temp file {filepath}: {e}")

        # Send tilbake voice-fil + metadata
        response_data = {
            "text": coach_text,
            "breath_analysis": breath_data,
            "audio_url": f"/download/{os.path.basename(voice_file)}",
            "phase": phase
        }

        logger.info(f"Coach response: '{coach_text}' (intensitet: {breath_data['intensitet']})")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in coach endpoint: {e}", exc_info=True)
        return jsonify({"error": "Intern serverfeil"}), 500

@app.route('/download/<filename>')
def download(filename):
    """Last ned generert voice-fil"""
    try:
        # Security: Prevent directory traversal
        if '..' in filename or '/' in filename:
            logger.warning(f"Attempted directory traversal: {filename}")
            return jsonify({"error": "Ugyldig filnavn"}), 400

        filepath = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(filepath):
            logger.info(f"Serving file: {filename}")
            return send_file(filepath, mimetype='audio/mpeg')

        logger.warning(f"File not found: {filename}")
        return jsonify({"error": "Fil ikke funnet"}), 404

    except Exception as e:
        logger.error(f"Error downloading file: {e}", exc_info=True)
        return jsonify({"error": "Intern serverfeil"}), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endepunkt ikke funnet"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Intern serverfeil"}), 500

# ============================================
# START SERVER
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting Treningscoach Backend v1.1.0")
    logger.info(f"Port: {port}, Debug: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug)
