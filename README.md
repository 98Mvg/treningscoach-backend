# 🏋️ Treningscoach Backend

Backend for iOS voice-coaching app.

## Funksjonalitet:
- Mottar lydopptak fra app
- Analyserer pust (volum, tempo, stillhet)
- Genererer coach-respons
- Sender voice tilbake til app

## API Endepunkter:

### GET /
Hjemmeside - viser at backend kjører

### GET /health
Helse-sjekk

### POST /analyze
Analyser lydopptak
- Input: audio (WAV/MP3 fil)
- Output: JSON med puste-data

### POST /coach
Få coach-respons
- Input: audio (WAV fil), phase (warmup/intense/cooldown)
- Output: JSON med voice URL og metadata

## Lokal test:
```bash
python main.py
```

Backend kjører på http://localhost:5000
