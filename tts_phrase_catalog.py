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

# =============================================================================
# STATIC PHRASES — can be pre-generated as-is
# =============================================================================

PHRASE_CATALOG = [

    # -----------------------------------------------------------------
    # WELCOME — config.py WELCOME_MESSAGES (personal_trainer)
    # -----------------------------------------------------------------

    # standard
    {"id": "welcome.standard.1", "en": "Good to see you. Let's start with some easy movement and build from there.", "no": "Fint at du er her. Vi starter rolig og bygger derfra.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.standard.2", "en": "Ready when you are. Take a breath, settle in, and we'll ease into it.", "no": "Klar når du er. Ta et pust, finn roen, så setter vi i gang.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.standard.3", "en": "Nice timing. Let's warm up properly and set the tone for a good session.", "no": "Bra timing. La oss varme opp ordentlig og legge grunnlaget.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.standard.4", "en": "Let's get moving. Controlled pace to start, then we'll find your rhythm.", "no": "La oss komme i gang. Kontrollert tempo til å begynne med.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.standard.5", "en": "Welcome back. Focus on how your body feels and we'll build from there.", "no": "Velkommen tilbake. Kjenn på kroppen så bygger vi derfra.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.standard.6", "en": "Alright, let's begin. Smooth and steady, no rush.", "no": "Ok, la oss begynne. Rolig og jevnt, uten stress.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.standard.7", "en": "Good call showing up. Start easy, the intensity will come naturally.", "no": "Bra at du dukket opp. Start rolig, intensiteten kommer naturlig.", "persona": "personal_trainer", "priority": "core"},

    # beginner_friendly
    {"id": "welcome.beginner.1", "en": "Great that you're here. We'll start slow and keep it simple.", "no": "Fint at du er her. Vi starter sakte og holder det enkelt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.beginner.2", "en": "Welcome. Just focus on breathing and moving at your own pace.", "no": "Velkommen. Bare fokuser på pusten og beveg deg i ditt tempo.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.beginner.3", "en": "Let's begin easy. No pressure, just getting your body warmed up.", "no": "La oss starte rolig. Ingen press, bare få kroppen varm.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.beginner.4", "en": "Nice to have you. Take it one step at a time, I'll guide you through.", "no": "Godt å ha deg her. Ett steg om gangen, jeg guider deg.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.beginner.5", "en": "You're here, that's the hardest part. Now let's ease into it together.", "no": "Du er her, det er det vanskeligste. Nå tar vi det rolig sammen.", "persona": "personal_trainer", "priority": "core"},

    # breath_aware
    {"id": "welcome.breath.1", "en": "Take a moment. Deep breath in, slow breath out. Now let's begin.", "no": "Ta et øyeblikk. Dyp innpust, rolig utpust. Nå begynner vi.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.breath.2", "en": "Start by finding your breath. Shoulders down, chest open, easy pace.", "no": "Start med å finne pusten. Skuldrene ned, brystet åpent, rolig tempo.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.breath.3", "en": "Let's connect with your breathing first. Everything else follows from there.", "no": "La oss koble på pusten først. Alt annet følger derfra.", "persona": "personal_trainer", "priority": "core"},
    {"id": "welcome.breath.4", "en": "Settle your breath, relax your body. We'll build the intensity gradually.", "no": "Finn roen i pusten, slapp av kroppen. Vi bygger intensiteten gradvis.", "persona": "personal_trainer", "priority": "core"},

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

    # -----------------------------------------------------------------
    # ZONE EVENTS — zone_event_motor.py (fixed text, no variables)
    # -----------------------------------------------------------------

    {"id": "zone.watch_disconnected.1", "en": "Watch disconnected. I'll coach using breathing and timing.", "no": "Klokken er frakoblet. Jeg coacher videre med pust og timing.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.no_sensors.1", "en": "No sensors now. Run by feel.", "no": "Ingen sensorer nå. Løp på følelse.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.watch_restored.1", "en": "Watch restored. Zone coaching is back.", "no": "Klokken er tilbake. Sonecoaching er aktiv igjen.", "persona": "personal_trainer", "priority": "core"},

    # interval countdowns
    {"id": "zone.countdown.30", "en": "30 seconds left.", "no": "30 sekunder igjen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.countdown.15", "en": "15 seconds left.", "no": "15 sekunder igjen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.countdown.5", "en": "5 seconds left.", "no": "5 sekunder igjen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.countdown.start", "en": "Next interval now.", "no": "Neste drag nå.", "persona": "personal_trainer", "priority": "core"},

    # phase changes
    {"id": "zone.main_started.1", "en": "Main set now. Stay controlled.", "no": "Hoveddel nå. Hold kontroll.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.workout_finished.1", "en": "Workout finished. Nice work.", "no": "Økten er ferdig. Bra jobbet.", "persona": "personal_trainer", "priority": "core"},

    # HR signal
    {"id": "zone.hr_poor_enter.1", "en": "Heart-rate signal is weak right now. I'll coach using timing and breathing until it stabilizes. Tighten your watch strap.", "no": "Puls-signalet er svakt akkurat nå. Jeg coacher med timing og pust til det stabiliserer seg. Stram klokka litt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.hr_poor_exit.1", "en": "Heart-rate signal is stable again. Returning to zone coaching.", "no": "Pulsen er stabil igjen. Vi går tilbake til sonecoaching.", "persona": "personal_trainer", "priority": "core"},

    # above zone
    {"id": "zone.above.minimal.1", "en": "Ease off 10-15 seconds.", "no": "Litt ned 10-15 sekunder.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.above.default.1", "en": "Ease off and regain control.", "no": "Litt ned. Finn kontroll.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.above_ease.minimal.1", "en": "HR still climbing. Ease down.", "no": "Pulsen stiger. Rolig ned.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.above_ease.default.1", "en": "Your heart rate is still climbing. Ease down for 20 seconds.", "no": "Pulsen stiger fortsatt. Ro ned 20 sekunder.", "persona": "personal_trainer", "priority": "core"},

    # below zone
    {"id": "zone.below.minimal.1", "en": "Build slightly now.", "no": "Bygg litt opp nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.below.default.1", "en": "Build effort slightly now.", "no": "Litt opp i innsats nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.below_push.minimal.1", "en": "You're moving. Add a little.", "no": "Du er i gang. Litt opp.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.below_push.default.1", "en": "You're moving well. Add a little effort and keep the flow.", "no": "Du er i gang. Øk litt nå og hold flyten.", "persona": "personal_trainer", "priority": "core"},

    # in zone
    {"id": "zone.in_zone.minimal.1", "en": "Good. Stay here.", "no": "Bra. Hold deg her.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.in_zone.default.1", "en": "Nice. Hold this zone.", "no": "Der ja. Hold deg i denne sonen.", "persona": "personal_trainer", "priority": "core"},

    # phase transitions
    {"id": "zone.phase.work.default.1", "en": "Work block. Controlled hard.", "no": "Dragstart. Kontroller hardt.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.phase.work.motivational.1", "en": "New work block. Controlled hard now.", "no": "Nytt drag. Sterk kontroll nå.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.phase.rest.1", "en": "Recovery block. Easy jog.", "no": "Pauseblokk. Rolig jogg.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.phase.warmup.1", "en": "Warm-up now. Keep it easy.", "no": "Oppvarming nå. Hold det lett.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.phase.cooldown.1", "en": "Cooldown now. Bring heart rate down.", "no": "Nedjogg nå. Senk pulsen.", "persona": "personal_trainer", "priority": "core"},

    # pause detection
    {"id": "zone.pause.detected.1", "en": "Looks like you paused. Start easy again when ready.", "no": "Du ser ut til å ha stoppet. Start rolig igjen når du er klar.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.pause.resumed.1", "en": "Good, you're moving again. Keep it controlled.", "no": "Bra, du er i gang igjen. Hold rolig kontroll.", "persona": "personal_trainer", "priority": "core"},

    # max silence overrides
    {"id": "zone.silence.work.1", "en": "Stay controlled. One rep at a time.", "no": "Hold kontroll. Ett drag av gangen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.silence.rest.1", "en": "Stay easy between reps.", "no": "Rolig mellom dragene.", "persona": "personal_trainer", "priority": "core"},
    {"id": "zone.silence.default.1", "en": "Hold steady rhythm.", "no": "Hold jevn rytme.", "persona": "personal_trainer", "priority": "core"},

    # -----------------------------------------------------------------
    # MOTIVATION — general encouragement cues
    # -----------------------------------------------------------------

    {"id": "motivation.1", "en": "You're doing great.", "no": "Du er kjempeflink.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.2", "en": "Strong work. Keep it up.", "no": "Sterkt. Fortsett slik.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.3", "en": "That's the effort I want to see.", "no": "Det er innsatsen jeg vil se.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.4", "en": "One step at a time. You got this.", "no": "Ett steg om gangen. Du klarer det.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.5", "en": "Discipline beats motivation. Keep going.", "no": "Disiplin slår motivasjon. Fortsett.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.6", "en": "This is where it counts.", "no": "Det er nå det gjelder.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.7", "en": "You showed up. Now finish it.", "no": "Du møtte opp. Nå fullfører du.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.8", "en": "Trust the process.", "no": "Stol på prosessen.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.9", "en": "Every rep matters.", "no": "Hvert steg teller.", "persona": "personal_trainer", "priority": "core"},
    {"id": "motivation.10", "en": "Finish what you started.", "no": "Fullfør det du begynte på.", "persona": "personal_trainer", "priority": "core"},
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
                "text": phrase[language],
                "persona": phrase["persona"],
                "priority": phrase["priority"],
            })
        else:
            for lang in ("en", "no"):
                results.append({
                    "id": phrase["id"],
                    "text": phrase[lang],
                    "language": lang,
                    "persona": phrase["persona"],
                    "priority": phrase["priority"],
                })
    return results


def get_core_phrases(language: str = None) -> list:
    """Get only core priority phrases."""
    return [p for p in get_all_static_phrases(language) if p["priority"] == "core"]


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
