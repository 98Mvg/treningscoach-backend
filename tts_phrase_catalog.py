"""
TTS Phrase Catalog — Single source of truth for all pre-generable audio.

Every entry has:
  - id:       Stable ID (format: {source}.{category}.{sub}.{n})
  - en:       English text
  - no:       Norwegian text
  - persona:  Which voice persona to use ("personal_trainer" or "toxic_mode")
  - priority: "core" = must be in every audio pack, "extended" = nice to have

IDs are STABLE — once assigned, never reuse or renumber.
Add new phrases at the end of each section with the next number.

Dynamic phrases (containing {variables}) are listed in DYNAMIC_TEMPLATES
and must be rendered per-value before generation.

Usage:
    from tts_phrase_catalog import PHRASE_CATALOG, DYNAMIC_TEMPLATES
    for phrase in PHRASE_CATALOG:
        print(phrase["id"], phrase["en"])
"""

import re

# =============================================================================
# STATIC PHRASES — can be pre-generated as-is
# =============================================================================

PHRASE_CATALOG = [
    # -----------------------------------------------------------------
    # COACH — config.py COACH_MESSAGES (personal_trainer)
    # -----------------------------------------------------------------

    {"id": "coach.critical.1", "en": "STOP! Breathe slowly. You're safe.", "no": "STOPP! Pust sakte. Du er trygg.", "persona": "personal_trainer", "priority": "core"},

    # warmup
    {"id": "coach.warmup.1", "en": "Welcome. Let's start slow. Find your rhythm.", "no": "Velkommen. La oss starte rolig. Finn rytmen din.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.warmup.2", "en": "Good. Breathe in, and out. Settle your shoulders.", "no": "Bra. Pust inn, og ut. Slapp av skuldrene.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.warmup.3", "en": "Steady now. Don't rush. Warmup first, intensity later.", "no": "Rolig nå. Ikke stress. Oppvarming først.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.warmup.4", "en": "Easy does it. Focus on breathing, not speed.", "no": "Ta det med ro. Fokuser på pusten.", "persona": "personal_trainer", "priority": "core"},

    # cooldown
    {"id": "coach.cooldown.1", "en": "Well done. Let the breath settle. You earned it.", "no": "Bra jobbet. La pusten roe seg. Du fortjener det.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.cooldown.2", "en": "Relax. Slow it down. Shoulder and chest relaxed.", "no": "Slapp av. Senk tempoet. Skuldre og bryst avslappet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.cooldown.3", "en": "Good session. Keep calm and controlled.", "no": "God økt. Hold deg rolig og kontrollert.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.cooldown.4", "en": "Steady breathing. That's how we finish strong.", "no": "Jevn pust. Slik avslutter vi sterkt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.cooldown.5", "en": "Nice work. You controlled your effort well.", "no": "Bra jobbet. Du kontrollerte innsatsen godt.", "persona": "personal_trainer", "priority": "core"},

    # intense.calm
    {"id": "coach.intense.calm.1", "en": "Maintain control. Pace yourself. Don't overdo it.", "no": "Behold kontrollen. Hold tempoet. Ikke overdrive.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.calm.2", "en": "Good. Keep that rhythm. Slightly faster, not frantic.", "no": "Bra. Hold rytmen. Litt raskere, ikke hektisk.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.calm.3", "en": "PUSH! Harder!", "no": "TRYKK! Hardere!", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.calm.4", "en": "You got more!", "no": "Du har mer!", "persona": "personal_trainer", "priority": "core"},

    # intense.moderate
    {"id": "coach.intense.moderate.1", "en": "Good. Keep that rhythm. Slightly faster, not frantic.", "no": "Bra. Hold rytmen. Litt raskere, ikke hektisk.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.moderate.2", "en": "Steady arms, steady breath. That's it.", "no": "Sterke armer, stø pust. Der ja.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.moderate.3", "en": "Keep going! Don't stop!", "no": "Fortsett! Ikke stopp!", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.moderate.4", "en": "Good! Hold the pace!", "no": "Bra! Hold tempoet!", "persona": "personal_trainer", "priority": "core"},

    # intense.intense
    {"id": "coach.intense.intense.1", "en": "Breathing quickened. Slow down a touch.", "no": "Pusten øker. Senk litt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.intense.2", "en": "Maintain control. Pace yourself. Don't overdo it.", "no": "Behold kontrollen. Hold tempoet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.intense.3", "en": "One more interval like this and you're done. Focus.", "no": "En runde til slik, så er du ferdig. Fokus.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.intense.intense.4", "en": "YES! Hold on! Ten more!", "no": "JA! Hold ut! Ti til!", "persona": "personal_trainer", "priority": "core"},

    # -----------------------------------------------------------------
    # CONTINUOUS — config.py CONTINUOUS_COACH_MESSAGES (personal_trainer)
    # -----------------------------------------------------------------

    # critical
    {"id": "cont.critical.1", "en": "STOP!", "no": "STOPP!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.critical.2", "en": "Breathe slow!", "no": "Pust rolig!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.critical.3", "en": "Easy now!", "no": "Ta det rolig!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.critical.4", "en": "Slow down!", "no": "Senk farten!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.critical.5", "en": "Too hard!", "no": "For hardt!", "persona": "personal_trainer", "priority": "core"},

    # warmup
    {"id": "cont.warmup.1", "en": "Easy pace, nice start.", "no": "Rolig tempo, fin start.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.warmup.2", "en": "Steady, good warmup.", "no": "Jevnt, god oppvarming.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.warmup.3", "en": "Gentle, keep warming up.", "no": "Rolig, fortsett oppvarmingen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.warmup.4", "en": "Nice and easy.", "no": "Fint og rolig.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.warmup.5", "en": "Perfect warmup pace.", "no": "Perfekt oppvarmingstempo.", "persona": "personal_trainer", "priority": "core"},

    # cooldown
    {"id": "cont.cooldown.1", "en": "Bring it down, easy now.", "no": "Senk tempoet, ta det rolig nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.cooldown.2", "en": "Slow breaths, good cooldown.", "no": "Rolige pust, god nedkjøling.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.cooldown.3", "en": "Ease off, nice work.", "no": "Slipp av, bra jobbet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.cooldown.4", "en": "Almost done, slow it.", "no": "Nesten ferdig, senk farten.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.cooldown.5", "en": "Perfect, keep slowing down.", "no": "Perfekt, fortsett å roe ned.", "persona": "personal_trainer", "priority": "core"},

    # intense.calm
    {"id": "cont.intense.calm.1", "en": "You can push harder!", "no": "Du kan presse hardere!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.calm.2", "en": "More effort, you got this!", "no": "Mer innsats, du klarer det!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.calm.3", "en": "Speed up a bit!", "no": "Øk tempoet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.calm.4", "en": "Give me more power!", "no": "Mer press nå!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.calm.5", "en": "Let's pick up the pace!", "no": "La oss øke farten!", "persona": "personal_trainer", "priority": "core"},

    # intense.moderate
    {"id": "cont.intense.mod.1", "en": "Keep going, good pace!", "no": "Fortsett, godt tempo!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.mod.2", "en": "Stay with it!", "no": "Hold deg fokusert!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.mod.3", "en": "Nice rhythm, maintain!", "no": "Bra tempo!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.mod.4", "en": "You got this!", "no": "Du klarer det!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.mod.5", "en": "Good work, keep steady!", "no": "Bra jobba! Hold jevnt tempo.", "persona": "personal_trainer", "priority": "core"},

    # intense.intense
    {"id": "cont.intense.intense.1", "en": "Perfect! Hold it!", "no": "Perfekt! Hold tempoet!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.intense.2", "en": "Yes! Strong!", "no": "Ja! Sterkt!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.intense.3", "en": "Keep this!", "no": "Behold dette!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.intense.4", "en": "Excellent work!", "no": "Utmerket jobbet!", "persona": "personal_trainer", "priority": "core"},
    {"id": "cont.intense.intense.5", "en": "Ten more seconds!", "no": "Ti sekunder til!", "persona": "personal_trainer", "priority": "core"},

    # -----------------------------------------------------------------
    # TOXIC MODE — config.py TOXIC_MODE_MESSAGES
    # -----------------------------------------------------------------

    # warmup
    {"id": "toxic.warmup.1", "en": "Warming up?! We're WASTING TIME!", "no": "Oppvarming?! Vi KASTER BORT TID!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.warmup.2", "en": "Move FASTER or go home!", "no": "Beveg deg RASKERE eller gå hjem!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.warmup.3", "en": "My GRANDMOTHER warms up faster!", "no": "BESTEMORA mi varmer opp raskere!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.warmup.4", "en": "This is PATHETIC! Let's GO!", "no": "Dette er PATETISK! La oss KJØRE!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.warmup.5", "en": "You call this a warmup? I call it a NAP!", "no": "Kaller du dette oppvarming? Jeg kaller det en LITEN BLUND!", "persona": "toxic_mode", "priority": "extended"},

    # intense.calm
    {"id": "toxic.intense.calm.1", "en": "PATHETIC! My grandma pushes harder!", "no": "PATETISK! Bestemora mi presser hardere!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.calm.2", "en": "Are you even TRYING?! MOVE!", "no": "PRØVER du i det hele tatt?! BEVEG DEG!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.calm.3", "en": "I've seen SNAILS with more intensity!", "no": "Jeg har sett SNEGLER med mer intensitet!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.calm.4", "en": "Is that ALL you got?! EMBARRASSING!", "no": "Er det ALT du har?! PINLIG!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.calm.5", "en": "WAKE UP! This isn't a spa day!", "no": "VÅKN OPP! Dette er ikke en spa-dag!", "persona": "toxic_mode", "priority": "extended"},

    # intense.moderate
    {"id": "toxic.intense.mod.1", "en": "Barely acceptable. Give me MORE!", "no": "Så vidt godkjent. Gi meg MER!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.mod.2", "en": "You can do better than THAT!", "no": "Du kan bedre enn DET!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.mod.3", "en": "I'm NOT impressed yet. HARDER!", "no": "Jeg er IKKE imponert ennå. HARDERE!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.mod.4", "en": "Keep going or I'll double it!", "no": "Fortsett ellers dobler jeg det!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.mod.5", "en": "That's it?! Push HARDER!", "no": "Er det alt?! TRYKK HARDERE!", "persona": "toxic_mode", "priority": "extended"},

    # intense.intense
    {"id": "toxic.intense.intense.1", "en": "FINALLY! Was that so hard?!", "no": "ENDELIG! Var det så vanskelig?!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.intense.2", "en": "NOW we're talking! Don't you DARE slow down!", "no": "NÅ snakker vi! Ikke VÅG å senke farten!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.intense.3", "en": "THERE it is! About TIME!", "no": "DER er det! På TIDE!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.intense.4", "en": "YES! That's what I want! MORE!", "no": "JA! Det er det jeg vil ha! MER!", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.intense.intense.5", "en": "Not bad. But I want BETTER!", "no": "Ikke verst. Men jeg vil ha BEDRE!", "persona": "toxic_mode", "priority": "extended"},

    # cooldown
    {"id": "toxic.cooldown.1", "en": "Done already?! Fine. You EARNED this break.", "no": "Ferdig allerede?! Greit. Du FORTJENTE denne pausen.", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.cooldown.2", "en": "Okay, okay. You survived. Barely.", "no": "Ok, ok. Du overlevde. Så vidt.", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.cooldown.3", "en": "Not the worst I've seen. Rest up.", "no": "Ikke det verste jeg har sett. Hvil deg.", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.cooldown.4", "en": "Acceptable performance. BARELY acceptable.", "no": "Godkjent prestasjon. Så vidt godkjent.", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.cooldown.5", "en": "Alright, breathe. You'll need it for next time.", "no": "Greit, pust. Du trenger det til neste gang.", "persona": "toxic_mode", "priority": "extended"},

    # critical (toxic drops the act)
    {"id": "toxic.critical.1", "en": "Alright, real talk. Breathe. Safety first.", "no": "Ok, alvor nå. Pust. Sikkerhet først.", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.critical.2", "en": "Okay, stop. I'm tough, not stupid. Rest.", "no": "Ok, stopp. Jeg er toff, ikke dum. Hvil.", "persona": "toxic_mode", "priority": "extended"},
    {"id": "toxic.critical.3", "en": "Hey. Real break. Breathe slow. I mean it.", "no": "Hei. Ordentlig pause. Pust rolig. Jeg mener det.", "persona": "toxic_mode", "priority": "extended"},

    # -----------------------------------------------------------------
    # BREATHING TIMELINE — breathing_timeline.py
    # -----------------------------------------------------------------

    # prep
    {"id": "breath.prep.1", "en": "Alright, let's get ready.", "no": "Greit, la oss gjøre oss klare.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.prep.2", "en": "Drink some water if you need to.", "no": "Drikk litt vann om du trenger.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.prep.3", "en": "Stretch out anything that feels tight.", "no": "Tøy ut det som kjennes stramt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.prep.4", "en": "We start in a moment. Take a deep breath.", "no": "Vi starter snart. Ta et dypt pust.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.prep.5", "en": "Remember: if you need to stop at any point, just stop. Listen to your body.", "no": "Husk: om du trenger å stoppe, bare stopp. Lytt til kroppen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.prep.6", "en": "Shake it out. Loosen up.", "no": "Rist det ut. Slapp av.", "persona": "personal_trainer", "priority": "core"},

    # prep safety
    {"id": "breath.prep.safety.1", "en": "If anything feels wrong during the workout, stop immediately. Your safety comes first.", "no": "Hvis noe føles feil under økten, stopp med en gang. Din sikkerhet kommer først.", "persona": "personal_trainer", "priority": "core"},

    # warmup
    {"id": "breath.warmup.1", "en": "Find your rhythm. Steady breaths.", "no": "Finn rytmen. Jevne pust.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.warmup.2", "en": "Easy breathing. Let it flow.", "no": "Rolig pust. La det flyte.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.warmup.3", "en": "Shoulders down, chest open.", "no": "Skuldrene ned, brystet åpent.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.warmup.4", "en": "Nice and controlled. Build slowly.", "no": "Fint og kontrollert. Bygg sakte.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.warmup.5", "en": "Breathe through the nose if you can.", "no": "Pust gjennom nesen om du kan.", "persona": "personal_trainer", "priority": "core"},

    # intense
    {"id": "breath.intense.1", "en": "Breathe through it.", "no": "Pust gjennom det.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.intense.2", "en": "Strong exhale. Power.", "no": "Sterk utpust. Kraft.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.intense.3", "en": "Don't hold your breath.", "no": "Ikke hold pusten.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.intense.4", "en": "Exhale on the effort.", "no": "Pust ut på innsatsen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.intense.5", "en": "Keep breathing. Stay with it.", "no": "Fortsett å puste. Hold deg i det.", "persona": "personal_trainer", "priority": "core"},

    # recovery
    {"id": "breath.recovery.1", "en": "Slow it down. In four... out six.", "no": "Senk tempoet. Inn fire... ut seks.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.recovery.2", "en": "Long exhale. Let the tension go.", "no": "Lang utpust. Slipp spenningen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.recovery.3", "en": "Recovery breath. Nice and slow.", "no": "Hvilepust. Fint og rolig.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.recovery.4", "en": "Breathe deep. You earned this.", "no": "Pust dypt. Du fortjente dette.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.recovery.5", "en": "Slow nose breathing. Good.", "no": "Rolig nesepust. Bra.", "persona": "personal_trainer", "priority": "core"},

    # cooldown
    {"id": "breath.cooldown.1", "en": "Deep breath in... slow breath out.", "no": "Dypt inn... sakte ut.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.cooldown.2", "en": "You earned this. Breathe deep.", "no": "Du fortjente dette. Pust dypt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.cooldown.3", "en": "Let your breathing return to normal.", "no": "La pusten komme tilbake til normalt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.cooldown.4", "en": "Relax everything. Just breathe.", "no": "Slapp av alt. Bare pust.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.cooldown.5", "en": "Great session. Wind it down.", "no": "Bra økt. Ro det ned.", "persona": "personal_trainer", "priority": "core"},

    # interrupts
    {"id": "breath.interrupt.cant_breathe.1", "en": "That's okay. Slow way down. Breathe through your nose.", "no": "Det er greit. Senk farten. Pust gjennom nesen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.interrupt.slow_down.1", "en": "Slowing down. Match my count. In... two... three...", "no": "Vi senker tempoet. Følg tellingen. Inn... to... tre...", "persona": "personal_trainer", "priority": "core"},
    {"id": "breath.interrupt.dizzy.1", "en": "Stop moving. Sit down if you need to. Slow nose breathing.", "no": "Stopp. Sett deg ned om du trenger. Rolig nesepust.", "persona": "personal_trainer", "priority": "core"},

    # wake acknowledgements (local, instant)
    {"id": "wake_ack.en.default", "en": "Yes?", "no": "Yes?", "persona": "personal_trainer", "priority": "core"},
    {"id": "wake_ack.no.default", "en": "Ja?", "no": "Ja?", "persona": "personal_trainer", "priority": "core"},
    # wake acknowledgement candidates (manual review/promotion set)
    {"id": "wake_ack.en.candidate.1", "en": "Listening.", "no": "Listening.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.2", "en": "Go on.", "no": "Go on.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.3", "en": "Yep?", "no": "Yep?", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.4", "en": "Tell me.", "no": "Tell me.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.5", "en": "Ready.", "no": "Ready.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.6", "en": "Go.", "no": "Go.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.7", "en": "I'm here.", "no": "I'm here.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.8", "en": "Speak.", "no": "Speak.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.9", "en": "Alright.", "no": "Alright.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.10", "en": "Go ahead.", "no": "Go ahead.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.11", "en": "Okay.", "no": "Okay.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.12", "en": "I'm listening.", "no": "I'm listening.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.13", "en": "What's up?", "no": "What's up?", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.14", "en": "Talk to me.", "no": "Talk to me.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.15", "en": "Let's go.", "no": "Let's go.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.16", "en": "Talk.", "no": "Talk.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.17", "en": "Hit me.", "no": "Hit me.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.18", "en": "What's good?", "no": "What's good?", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.en.candidate.19", "en": "Go for it.", "no": "Go for it.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.no.candidate.1", "en": "Ja?", "no": "Ja?", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.no.candidate.2", "en": "Klar.", "no": "Klar.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.no.candidate.3", "en": "Jeg hører.", "no": "Jeg hører.", "persona": "personal_trainer", "priority": "extended"},
    {"id": "wake_ack.no.candidate.4", "en": "Hva skjer?", "no": "Hva skjer?", "persona": "personal_trainer", "priority": "extended"},

    # -----------------------------------------------------------------
    # ZONE EVENTS — zone_event_motor.py (fixed text, no variables)
    # -----------------------------------------------------------------

    {"id": "zone.watch_disconnected.1", "en": "Watch disconnected", "no": "Pulsklokken ble frakoblet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.no_sensors.1", "en": "Coaching by breath.", "no": "Coacher med pust.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.watch_restored.1", "en": "Watch connected and heart rate is back.", "no": "Klokken er tilkoblet, og pulsen er tilbake.", "persona": "personal_trainer", "priority": "core"},

    # interval countdowns
    {"id": "zone.countdown.30", "en": "30 seconds left.", "no": "30 sekunder.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.countdown.15", "en": "15", "no": "15", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.countdown.5", "en": "5!", "no": "fem", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.countdown.start", "en": "Go", "no": "Start", "persona": "personal_trainer", "priority": "core"},

    # phase changes
    {"id": "zone.main_started.1", "en": "Main set now.", "no": "Nå er du i hoveddelen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.workout_finished.1", "en": "Workout finished. Nice work.", "no": "Økten er ferdig. Bra jobbet.", "persona": "personal_trainer", "priority": "core"},

    # HR signal
    {"id": "zone.hr_poor_enter.1", "en": "Heart rate signal is weak.", "no": "Pulssignalet er svakt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.hr_poor_exit.1", "en": "Heart rate is back.", "no": "Pulsen er tilbake.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.hr_poor_timing.1", "en": "No heart rate signal. I will continue coaching", "no": "Ingen pulssignal. Jeg fortsetter å coache", "persona": "personal_trainer", "priority": "core"},

    # above zone
    {"id": "zone.above.minimal.1", "en": "Ease off 10-15 seconds.", "no": "Litt ned 10-15 sekunder.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.above.default.1", "en": "Ease back slightly.", "no": "Ro ned litt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.above_ease.minimal.1", "en": "HR still climbing. Ease down.", "no": "Pulsen stiger. Rolig ned.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.above_ease.default.1", "en": "Still high. Ease down 20 seconds.", "no": "Fortsatt høy. Ro ned 20 sekunder.", "persona": "personal_trainer", "priority": "core"},

    # below zone
    {"id": "zone.below.minimal.1", "en": "Build slightly now.", "no": "Bygg litt opp nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.below.default.1", "en": "Pick it up.", "no": "Øk litt nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.below_push.minimal.1", "en": "You're moving. Add a little.", "no": "Du er i gang. Litt opp.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.below_push.default.1", "en": "You're moving. Pick it up slightly.", "no": "Du er i gang. Øk litt.", "persona": "personal_trainer", "priority": "core"},

    # in zone
    {"id": "zone.in_zone.minimal.1", "en": "Good. Stay here.", "no": "Bli her.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.in_zone.default.1", "en": "Stay right here.", "no": "Bli her.", "persona": "personal_trainer", "priority": "core"},

    # phase transitions
    {"id": "zone.phase.work.default.1", "en": "Work starts now.", "no": "Nå begynner innsatsen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.phase.work.motivational.1", "en": "Time to work.", "no": "Nå jobber vi.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.phase.rest.1", "en": "Recovery now.", "no": "Pause nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.phase.warmup.1", "en": "Prepare for the session.", "no": "Forbered deg på økten.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.phase.cooldown.1", "en": "Cooldown now.", "no": "Nå roer vi ned.", "persona": "personal_trainer", "priority": "core"},

    # pause detection
    {"id": "zone.pause.detected.1", "en": "Paused session", "no": "Pauset økten.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.pause.resumed.1", "en": "You're moving again.", "no": "Du er i gang igjen.", "persona": "personal_trainer", "priority": "core"},

    # structure-driven instruction (no live HR)
    {"id": "zone.structure.work.1", "en": "Pick it up now.", "no": "Kjør på nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.structure.recovery.1", "en": "Ease back and recover.", "no": "Ro ned og hent deg inn.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.structure.steady.1", "en": "Settle into the pace.", "no": "Finn rytmen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.structure.steady.2", "en": "Stay with the rhythm.", "no": "Bli i rytmen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.structure.steady.3", "en": "Stay smooth and relaxed.", "no": "Rolig og avslappet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.structure.steady.4", "en": "Control the effort here.", "no": "Kontroll på innsatsen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.structure.steady.5", "en": "Keep the pace steady.", "no": "Hold tempoet jevnt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.structure.steady.6", "en": "Hold the phase.", "no": "Hold det her.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.structure.finish.1", "en": "Final push now!", "no": "Trykk til nå!", "persona": "personal_trainer", "priority": "core"},

    # max silence overrides
    {"id": "zone.silence.work.1", "en": "Hold the rhythm.", "no": "Hold rytmen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.silence.rest.1", "en": "Relax your shoulders.", "no": "Senk skuldrene.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.silence.default.1", "en": "Find your pace.", "no": "Finn rytmen.", "persona": "personal_trainer", "priority": "core"},

    # Go-by-feel fallback (no HR, no reliable breath) — phase-aware
    {"id": "zone.feel.easy_run.1", "en": "Steady effort. Stay comfortable.", "no": "Jevn innsats. Hold det behagelig.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.easy_run.2", "en": "Find your rhythm and hold it.", "no": "Finn rytmen din og hold den.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.easy_run.3", "en": "Easy and controlled. You set the pace.", "no": "Rolig og kontrollert. Du bestemmer tempoet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.work.1", "en": "Push hard but controlled.", "no": "Hold en jevn rytme", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.work.2", "en": "Strong effort now. Stay focused.", "no": "Sterk innsats nå. Hold fokus.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.recovery.1", "en": "Ease off. Let your body recover.", "no": "Slipp av. La kroppen hente seg inn.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.feel.recovery.2", "en": "Relax and breathe. Recovery counts.", "no": "Slapp av og pust. Hvile teller.", "persona": "personal_trainer", "priority": "core"},

    # Breath guidance fallback (no HR, breath reliable)
    {"id": "zone.breath.easy_run.1", "en": "Match your breathing to your pace.", "no": "Tilpass pusten til tempoet.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.breath.easy_run.2", "en": "Smooth breaths. You're doing well.", "no": "Jevn pust. Du gjør det bra.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.breath.work.1", "en": "Breathe through the effort.", "no": "Herlig", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.breath.recovery.1", "en": "Slow your breathing down.", "no": "Senk pustetakten.", "persona": "personal_trainer", "priority": "core"},

    # -----------------------------------------------------------------
    # MOTIVATION — general encouragement cues
    # -----------------------------------------------------------------

    {"id": "motivation.1", "en": "Nice work!", "no": "Hold det sterkt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.2", "en": "Keep it up.", "no": "Bra jobba!", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.3", "en": "That's the effort I want to see.", "no": "Det skal kjennes litt. Det er prisen for endring..", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.4", "en": "One step at a time. You got this.", "no": "Ett steg om gangen. Du klarer det.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.5", "en": "Discipline beats motivation. Keep going.", "no": "Disiplin slår motivasjon. Fortsett.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.6", "en": "This is where it counts.", "no": "Det er nå det gjelder.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.7", "en": "You showed up. thats the hard part.", "no": "Du møtte opp. Det er det vanskelige.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.8", "en": "Trust the process.", "no": "Stol på prosessen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.9", "en": "Every rep matters.", "no": "Hvert steg teller.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.10", "en": "Finish what you started.", "no": "Fullfør det du begynte på.", "persona": "personal_trainer", "priority": "core"},

    # -----------------------------------------------------------------
    # NORWEGIAN-NATIVE COACHING — signature phrases from persona_manager
    # Grouped by emotional mode: supportive → pressing → intense → peak
    # English equivalents are tone-matched, not literal translations.
    # -----------------------------------------------------------------

    # supportive (steady, grounded)
    {"id": "coach.no.supportive.1", "en": "Beautiful. Smooth and steady.", "no": "Nydelig. Jevnt og rolig.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.supportive.2", "en": "Focus on breath and rhythm.", "no": "Fokuser på pust og rytme.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.supportive.3", "en": "Come on now.", "no": "Kom igjen nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.supportive.4", "en": "Good. Breathe easy.", "no": "Bra. Pust rolig.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.supportive.5", "en": "Settle your pace.", "no": "Finn ditt tempo.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.supportive.6", "en": "Relax. You earned it.", "no": "Slapp av. Du fortjener det.", "persona": "personal_trainer", "priority": "core"},

    # pressing (challenge, direct)
    {"id": "coach.no.pressing.1", "en": "Nice work.", "no": "Bra jobba.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.pressing.2", "en": "Keep it steady.", "no": "Hold det jevnt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.pressing.3", "en": "Hold the rhythm.", "no": "Hold rytmen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.pressing.4", "en": "Good rhythm.", "no": "Bra rytme.", "persona": "personal_trainer", "priority": "core"},

    # intense (demanding, short commands)
    {"id": "coach.no.intense.1", "en": "All the way! Drive your legs!", "no": "Helt inn nå! Trøkk i beina!", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.intense.2", "en": "Time to work! Smooth and strong.", "no": "Nå må du jobbe! Jevnt og godt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.intense.3", "en": "One more. Don't stop.", "no": "En til. Ikke stopp.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.intense.4", "en": "Finish the rep. Now.", "no": "Fullfør draget. Nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.intense.5", "en": "Discipline. Execute.", "no": "Disiplin. Gjennomfør.", "persona": "personal_trainer", "priority": "core"},

    # peak (maximum urgency, ultra-short)
    {"id": "coach.no.peak.1", "en": "Finish strong!", "no": "Kjør på nå!", "persona": "personal_trainer", "priority": "core"},
    {"id": "coach.no.peak.2", "en": "All the way in.", "no": "Helt inn!", "persona": "personal_trainer", "priority": "core"},

    # -----------------------------------------------------------------
    # INTERVAL MOTIVATION — stage-based (rep_index determines stage)
    # Used by interval_in_target_sustained event in zone_event_motor.
    # -----------------------------------------------------------------

    # stage 1: supportive (rep 1)
    {"id": "interval.motivate.s1.1", "en": "Control your breath.", "no": "Kontroller pusten.", "persona": "personal_trainer", "priority": "core"},
    {"id": "interval.motivate.s1.2", "en": "Good start.", "no": "God start.", "persona": "personal_trainer", "priority": "core"},

    # stage 2: pressing (rep 2)
    {"id": "interval.motivate.s2.1", "en": "Nice work.", "no": "Bra jobba.", "persona": "personal_trainer", "priority": "core"},
    {"id": "interval.motivate.s2.2", "en": "Hold the rhythm.", "no": "Hold det sterkt.", "persona": "personal_trainer", "priority": "core"},

    # stage 3: intense (rep 3)
    {"id": "interval.motivate.s3.1", "en": "Perfect!", "no": "Hold rytmen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "interval.motivate.s3.2", "en": "Stay with it!", "no": "Stå i det!", "persona": "personal_trainer", "priority": "core"},

    # stage 4: peak (rep >= 4)
    {"id": "interval.motivate.s4.1", "en": "Finish strong!", "no": "Kjør på nå!", "persona": "personal_trainer", "priority": "core"},
    {"id": "interval.motivate.s4.2", "en": "All the way in.", "no": "Helt inn!", "persona": "personal_trainer", "priority": "core"},

    # -----------------------------------------------------------------
    # EASY-RUN MOTIVATION — stage-based (elapsed minutes determines stage)
    # Used by easy_run_in_target_sustained event in zone_event_motor.
    # -----------------------------------------------------------------

    # stage 1: supportive (0–20 min)
    {"id": "easy_run.motivate.s1.1", "en": "Focus on breath and rhythm.", "no": "Fokuser på pust og rytme.", "persona": "personal_trainer", "priority": "core"},
    {"id": "easy_run.motivate.s1.2", "en": "Settle your pace.", "no": "Finn ditt tempo.", "persona": "personal_trainer", "priority": "core"},

    # stage 2: pressing (20–40 min)
    {"id": "easy_run.motivate.s2.1", "en": "Good rhythm.", "no": "Bra rytme.", "persona": "personal_trainer", "priority": "core"},
    {"id": "easy_run.motivate.s2.2", "en": "Keep it steady.", "no": "Hold det jevnt.", "persona": "personal_trainer", "priority": "core"},

    # stage 3: intense (40–60 min)
    {"id": "easy_run.motivate.s3.1", "en": "Nice work!", "no": "Bra jobba!", "persona": "personal_trainer", "priority": "core"},
    {"id": "easy_run.motivate.s3.2", "en": "Keep it strong.", "no": "Herlig!", "persona": "personal_trainer", "priority": "core"},

    # stage 4: peak (60+ min)
    {"id": "easy_run.motivate.s4.1", "en": "Stay smooth.", "no": "Hold det rolig.", "persona": "personal_trainer", "priority": "core"},
    {"id": "easy_run.motivate.s4.2", "en": "Keep it steady.", "no": "Hold det jevnt.", "persona": "personal_trainer", "priority": "core"},
]


# =============================================================================
# DYNAMIC TEMPLATES — need variable substitution before generation
# =============================================================================
# These have {placeholders} and must be expanded for each common value.
# Pre-generate for the most common values only.

DYNAMIC_TEMPLATES = [
    # Breathing timeline countdown (common values: 5, 10, 15, 20, 30)
    {"id": "breath.countdown.1", "en": "Starting in {seconds} seconds.", "no": "Starter om {seconds} sekunder.", "persona": "personal_trainer", "variables": {"seconds": [5, 10, 15, 20, 30]}},
    {"id": "breath.countdown.2", "en": "{seconds} seconds. Ready?", "no": "{seconds} sekunder. Klar?", "persona": "personal_trainer", "variables": {"seconds": [5, 10, 15, 20, 30]}},
    {"id": "breath.countdown.3", "en": "Here we go in {seconds}.", "no": "Her kjører vi om {seconds}.", "persona": "personal_trainer", "variables": {"seconds": [5, 10, 15, 20, 30]}},

    # Zone events with BPM targets (common ranges)
    {"id": "zone.above.bpm.1", "en": "Back off to {target_low}-{target_high} bpm.", "no": "Rolig ned mot {target_low}-{target_high} bpm.", "persona": "personal_trainer", "variables": {"target_low": [120, 130, 140, 150], "target_high": [135, 145, 155, 165]}},
    {"id": "zone.below.bpm.1", "en": "Build toward {target_low}-{target_high} bpm.", "no": "Løft rolig mot {target_low}-{target_high} bpm.", "persona": "personal_trainer", "variables": {"target_low": [120, 130, 140, 150], "target_high": [135, 145, 155, 165]}},
]


# =============================================================================
# HELPERS
# =============================================================================

def get_all_static_phrases(language: str = None) -> list:
    """
    Get all static phrases, optionally filtered by language.

    Args:
        language: "en", "no", or None (both)

    Returns:
        List of dicts: {"id": ..., "text": ..., "persona": ..., "priority": ...}
    """
    results = []
    for phrase in PHRASE_CATALOG:
        if language:
            results.append({
                "id": phrase["id"],
                "language": language,
                "text": phrase[language],
                "persona": phrase["persona"],
                "priority": phrase["priority"],
            })
        else:
            for lang in ("en", "no"):
                results.append({
                    "id": phrase["id"],
                    "language": lang,
                    "text": phrase[lang],
                    "persona": phrase["persona"],
                    "priority": phrase["priority"],
                })
    return results


def get_core_phrases(language: str = None) -> list:
    """Get only core priority phrases."""
    return [p for p in get_all_static_phrases(language) if p["priority"] == "core"]


def get_phrase_by_id(phrase_id: str) -> dict | None:
    """Return a catalog phrase dict by exact ID."""
    for phrase in PHRASE_CATALOG:
        if str(phrase.get("id", "")).strip() == phrase_id:
            return phrase
    return None


def get_phrase_text(phrase_id: str, language: str) -> str | None:
    """Return phrase text for the given ID/language."""
    phrase = get_phrase_by_id(phrase_id)
    if not phrase:
        return None
    lang_key = (language or "en").strip().lower()
    if lang_key not in ("en", "no"):
        lang_key = "en"
    text = phrase.get(lang_key)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return None


def list_phrase_ids_by_prefix(prefix: str, persona: str | None = None) -> list[str]:
    """List phrase IDs matching a stable prefix, sorted by numeric suffix when present."""
    normalized_prefix = (prefix or "").strip()
    if not normalized_prefix:
        return []
    matches: list[str] = []
    for phrase in PHRASE_CATALOG:
        phrase_id = str(phrase.get("id", "")).strip()
        if not phrase_id.startswith(f"{normalized_prefix}."):
            continue
        if persona and str(phrase.get("persona", "")).strip() != persona:
            continue
        matches.append(phrase_id)

    def _sort_key(phrase_id: str) -> tuple:
        last_segment = phrase_id.split(".")[-1]
        if last_segment.isdigit():
            return phrase_id.rsplit(".", 1)[0], int(last_segment), phrase_id
        return phrase_id, 0, phrase_id

    return sorted(set(matches), key=_sort_key)


def validate_welcome_catalog(catalog: list[dict] | None = None) -> list[str]:
    """
    Validate welcome phrase IDs for XLSX + latest.json workflow.

    Rules:
    - IDs must match welcome.<group>.<n> format.
    - Numbering per group must be contiguous (1..N).
    - Each welcome entry must contain non-empty `en` and `no`.
    """
    source = catalog if catalog is not None else PHRASE_CATALOG
    errors: list[str] = []
    groups: dict[str, list[int]] = {}
    id_pattern = re.compile(r"^welcome\.([a-z_]+)\.(\d+)$")

    for phrase in source:
        phrase_id = str(phrase.get("id", "")).strip()
        if not phrase_id.startswith("welcome."):
            continue

        match = id_pattern.match(phrase_id)
        if not match:
            errors.append(f"Invalid welcome ID format: {phrase_id}")
            continue

        group = match.group(1)
        number = int(match.group(2))
        groups.setdefault(group, []).append(number)

        for lang in ("en", "no"):
            text = str(phrase.get(lang, "")).strip()
            if not text:
                errors.append(f"Missing {lang} text for {phrase_id}")

    if not groups:
        return errors

    for group, numbers in sorted(groups.items()):
        unique_numbers = sorted(set(numbers))
        duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
        if duplicates:
            errors.append(
                f"Duplicate numbering in welcome.{group}: {', '.join(str(n) for n in duplicates)}"
            )

        expected = list(range(1, max(unique_numbers) + 1))
        missing = [n for n in expected if n not in unique_numbers]
        if missing:
            errors.append(
                f"Non-contiguous numbering in welcome.{group}: missing {', '.join(str(n) for n in missing)}"
            )

    return errors


def expand_dynamic_templates() -> list:
    """
    Expand dynamic templates into concrete phrases for all variable combinations.

    Returns:
        List of dicts: {"id": "breath.countdown.1.5", "en": "Starting in 5 seconds.", ...}
    """
    expanded = []
    for tmpl in DYNAMIC_TEMPLATES:
        variables = tmpl["variables"]
        var_names = list(variables.keys())

        if len(var_names) == 1:
            key = var_names[0]
            for val in variables[key]:
                expanded.append({
                    "id": f"{tmpl['id']}.{val}",
                    "en": tmpl["en"].format(**{key: val}),
                    "no": tmpl["no"].format(**{key: val}),
                    "persona": tmpl["persona"],
                })
        elif len(var_names) == 2:
            # Pair by index (target_low[i] with target_high[i])
            k1, k2 = var_names
            for v1, v2 in zip(variables[k1], variables[k2]):
                expanded.append({
                    "id": f"{tmpl['id']}.{v1}_{v2}",
                    "en": tmpl["en"].format(**{k1: v1, k2: v2}),
                    "no": tmpl["no"].format(**{k1: v1, k2: v2}),
                    "persona": tmpl["persona"],
                })

    return expanded


# Quick stats
TOTAL_STATIC = len(PHRASE_CATALOG)
TOTAL_CORE = len([p for p in PHRASE_CATALOG if p["priority"] == "core"])
TOTAL_EXTENDED = TOTAL_STATIC - TOTAL_CORE
TOTAL_DYNAMIC_EXPANDED = len(expand_dynamic_templates())

if __name__ == "__main__":
    print(f"TTS Phrase Catalog Stats:")
    print(f"  Static phrases:    {TOTAL_STATIC} ({TOTAL_CORE} core + {TOTAL_EXTENDED} extended)")
    print(f"  Dynamic expanded:  {TOTAL_DYNAMIC_EXPANDED}")
    print(f"  Total generable:   {TOTAL_STATIC + TOTAL_DYNAMIC_EXPANDED}")
    print(f"  Per language:      {TOTAL_STATIC + TOTAL_DYNAMIC_EXPANDED} EN + {TOTAL_STATIC + TOTAL_DYNAMIC_EXPANDED} NO")
    print(f"  Total audio files: {(TOTAL_STATIC + TOTAL_DYNAMIC_EXPANDED) * 2}")
    print()
    print("Core phrases (EN):")
    for p in get_core_phrases("en")[:5]:
        print(f"  [{p['id']}] {p['text']}")
    print(f"  ... and {len(get_core_phrases('en')) - 5} more")
