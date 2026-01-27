# main.py - HOVEDFIL FOR TRENINGSCOACH BACKEND

from flask import Flask, request, send_file, jsonify
import os
import json
import wave
import math
import random
from datetime import datetime

app = Flask(__name__)

# Mapper for å lagre filer midlertidig
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

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
        print(f"Feil ved analyse: {e}")
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
        return "STOPP! Pust rolig. Du er trygg."

    # OPPVARMING
    if phase == "warmup":
        return random.choice([
            "Start rolig. Vi varmer opp.",
            "Bra. Hold denne farten.",
            "Rolig tempo. Fortsett."
        ])

    # NEDKJØLING
    if phase == "cooldown":
        return random.choice([
            "Ta ned farten.",
            "Pust rolig.",
            "Bra. Rolig ned."
        ])

    # HARD TRENING
    if intensitet == "rolig":
        return random.choice([
            "PUSH! Hardere!",
            "Du klarer mer!",
            "Raskere! Nå!"
        ])

    elif intensitet == "moderat":
        return random.choice([
            "Fortsett! Du har mer!",
            "Ikke stopp! Fortsett!",
            "Bra! Hold farten!"
        ])

    elif intensitet == "hard":
        return random.choice([
            "Ja! Hold ut! Ti til!",
            "Bra! Fortsett!",
            "Der ja! Fem sekunder!"
        ])

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
    """Hjemmeside - viser at backend kjører"""
    return """
    <h1>🏋️‍♂️ Treningscoach Backend</h1>
    <p>Backend kjører! ✅</p>
    <h3>Tilgjengelige endepunkter:</h3>
    <ul>
        <li>POST /analyze - Analyser lydopptak</li>
        <li>POST /coach - Få coach-respons</li>
        <li>GET /health - Helse-sjekk</li>
    </ul>
    """

@app.route('/health')
def health():
    """Enkel helse-sjekk for å se at serveren lever"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Mottar lydopptak fra app og analyserer pusten

    App sender: MP3/WAV fil
    Backend returnerer: JSON med puste-data
    """

    if 'audio' not in request.files:
        return jsonify({"error": "Ingen lydfil mottatt"}), 400

    audio_file = request.files['audio']

    # Lagre filen midlertidig
    filename = f"breath_{datetime.now().timestamp()}.wav"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(filepath)

    # Analyser pusten
    breath_data = analyze_breath(filepath)

    # Slett midlertidig fil
    try:
        os.remove(filepath)
    except:
        pass

    return jsonify(breath_data)

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

    if 'audio' not in request.files:
        return jsonify({"error": "Ingen lydfil mottatt"}), 400

    audio_file = request.files['audio']
    phase = request.form.get('phase', 'intense')

    # Lagre filen midlertidig
    filename = f"breath_{datetime.now().timestamp()}.wav"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(filepath)

    # Analyser pusten
    breath_data = analyze_breath(filepath)

    # Få coach-respons (tekst)
    coach_text = get_coach_response(breath_data, phase)

    # Generer voice (mock for nå)
    voice_file = generate_voice_mock(coach_text)

    # Slett midlertidig inndata-fil
    try:
        os.remove(filepath)
    except:
        pass

    # Send tilbake voice-fil + metadata
    response_data = {
        "text": coach_text,
        "breath_analysis": breath_data,
        "audio_url": f"/download/{os.path.basename(voice_file)}"
    }

    return jsonify(response_data)

@app.route('/download/<filename>')
def download(filename):
    """Last ned generert voice-fil"""
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='audio/mpeg')
    return jsonify({"error": "Fil ikke funnet"}), 404

# ============================================
# START SERVER
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
