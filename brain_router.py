#
# brain_router.py
# Routes coaching requests to the configured AI brain
#

import asyncio
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Dict, Any, Optional
import config


class BrainRouter:
    """
    Router that directs coaching requests to the active brain.

    This is the single point of contact for the iOS app/website.
    The app never knows which brain is active - it just talks to this router.

    STEP 4: Supports hybrid mode - Claude for patterns, config for speed.
    """
    _SEXUAL_EXPLICIT_TOKENS = {
        "sex", "sexual", "sexy", "porn", "porno", "nude", "nudes", "fetish",
        "seksuell", "naken", "intimate", "explicit",
    }
    _HARASSMENT_TOKENS = {
        "harass", "harassing", "bully", "bullying", "insult", "shame",
        "idiot", "stupid", "loser", "worthless",
        "trakassere", "trakassering", "mobbe", "mobbing", "dum", "verdiløs",
    }
    _PROTECTED_GROUP_TOKENS = {
        "race", "religion", "gender", "sexuality", "nationality", "disability", "age",
        "woman", "women", "man", "men", "gay", "lesbian", "trans", "muslim", "jew", "christian",
        "menn", "kvinner", "jøde", "kristen", "homofil",
        "hudfarge", "rase", "kjønn", "funksjonshemmet", "alder",
    }
    _HATE_TOKENS = {"hate", "racist", "racism", "homophobic", "sexist", "nazis", "nazi", "hater", "hateful"}
    _HATE_STRONG_TOKENS = {"racist", "racism", "homophobic", "sexist", "nazi", "nazis"}
    _HARMFUL_TOKENS = {
        "selfharm", "suicide", "kill", "overdose", "starve", "dangerous", "unsafe",
        "hurt", "harm", "violence", "violent", "drug", "drugs", "steroid",
        "selvskading", "selvskade", "selvmord", "sult", "skad", "vold", "narkotika", "steroider",
    }
    _HARMFUL_PATTERNS = (
        "hurt someone",
        "kill someone",
        "harm myself",
        "hjelp meg å skade",
        "hvordan skade",
        "how to hurt",
        "how to kill",
    )
    _DOMAIN_TOKENS = {
        "train", "training", "workout", "run", "running", "interval", "intervals", "cardio",
        "fitness", "exercise", "health", "body", "muscle", "protein", "nutrition", "diet",
        "calorie", "calories", "carb", "carbs", "fat", "hydrate", "hydration", "water",
        "recovery", "sleep", "stress", "injury", "sore", "soreness", "hr", "pulse", "heart",
        "pace", "zone", "zones", "vo2", "endurance", "strength", "mobility",
        "trening", "trene", "trenings", "okt", "økt", "lop", "løp", "intervall", "intervaller",
        "utholdenhet", "helse", "kropp", "muskel", "ernaering", "ernæring",
        "kosthold", "kalori", "kalorier", "karbo", "fett", "vaeske", "væske", "hydrering",
        "restitusjon", "sovn", "søvn", "skade", "stol", "støl", "puls", "hjerte", "tempo", "sone",
        "styrke", "mobilitet",
    }
    _WORKOUT_CONTEXT_PROMPT_EXACT = {
        "what should i do now?",
        "what should i do now",
        "what should i do?",
        "what should i do",
        "what now?",
        "what now",
        "what next?",
        "what next",
        "hva skal jeg gjøre nå?",
        "hva skal jeg gjøre nå",
        "hva skal jeg gjøre?",
        "hva skal jeg gjøre",
        "hva nå?",
        "hva nå",
    }
    _WORKOUT_CONTEXT_PROMPT_PREFIXES = (
        "what should i do",
        "what now",
        "what next",
        "how am i doing",
        "hva skal jeg gjøre",
        "hva nå",
        "hvordan ligger jeg an",
        "hvordan går det",
    )

    def __init__(self, brain_type: Optional[str] = None, use_hybrid: Optional[bool] = None):
        """
        Initialize router with specified brain type.

        Args:
            brain_type: "claude", "openai", "grok", "gemini", or "config" (if None, uses config.ACTIVE_BRAIN)
            use_hybrid: Enable hybrid mode (if None, uses config.USE_HYBRID_BRAIN)
        """
        self.use_priority_routing = getattr(config, "USE_PRIORITY_ROUTING", False)
        self.priority_brains = list(getattr(config, "BRAIN_PRIORITY", [])) if self.use_priority_routing else []

        # If brain_type is explicitly provided, prefer it over priority routing
        if brain_type is not None:
            self.use_priority_routing = False
            self.priority_brains = []
            self.brain_type = brain_type
        else:
            self.brain_type = "priority" if self.use_priority_routing else config.ACTIVE_BRAIN
        self.use_hybrid = use_hybrid if use_hybrid is not None else getattr(config, 'USE_HYBRID_BRAIN', False)
        self.brain = None
        self.claude_brain = None  # STEP 4: Keep Claude brain for patterns
        self.brain_pool = {}
        self.brain_stats = {}
        self.brain_last_outcome = {}
        self._recent_outputs_by_session = {}
        self.brain_cooldowns = {}
        self.last_route_meta = {
            "provider": "uninitialized",
            "source": "none",
            "status": "uninitialized",
            "mode": None,
            "timestamp": None,
        }
        self._talk_policy_rotation_state = {}
        strict_enabled = bool(getattr(config, "COACH_TALK_STRICT_SAFETY_ENABLED", True))
        rotate_enabled = bool(getattr(config, "COACH_TALK_POLICY_ROTATE_ENABLED", True))
        print(
            f"🛡️ COACH_TALK_POLICY enabled={str(strict_enabled).lower()} "
            f"rotate={str(rotate_enabled).lower()}"
        )
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_brain()

        # STEP 4: Initialize Claude brain for hybrid mode if enabled
        if self.use_hybrid and self.brain_type in ("config", "priority"):
            self._initialize_hybrid_claude()

    def _prune_expired_cooldowns(self) -> None:
        """Drop expired cooldown entries to keep state compact/observable."""
        if not self.brain_cooldowns:
            return
        now = time.time()
        expired = [name for name, until in self.brain_cooldowns.items() if until <= now]
        for name in expired:
            self.brain_cooldowns.pop(name, None)

    def _initialize_brain(self):
        """Initialize the active brain based on configuration."""
        if self.brain_type == "priority":
            print("✅ Brain Router: Priority routing enabled")
            self.brain = None
            return

        if self.brain_type == "claude":
            try:
                from brains.claude_brain import ClaudeBrain
                self.brain = ClaudeBrain()
                print(f"✅ Brain Router: Using Claude (model: {self.brain.model})")
            except Exception as e:
                print(f"⚠️ Brain Router: Failed to initialize Claude: {e}")
                print("⚠️ Brain Router: Falling back to config-based messages")
                self.brain_type = "config"

        elif self.brain_type == "openai":
            try:
                from brains.openai_brain import OpenAIBrain
                self.brain = OpenAIBrain()
                print(f"✅ Brain Router: Using OpenAI (model: {self.brain.model})")
            except Exception as e:
                print(f"⚠️ Brain Router: Failed to initialize OpenAI: {e}")
                print("⚠️ Brain Router: Falling back to config-based messages")
                self.brain_type = "config"

        elif self.brain_type == "grok":
            try:
                from brains.grok_brain import GrokBrain
                self.brain = GrokBrain()
                print(f"✅ Brain Router: Using Grok (model: {self.brain.model})")
            except Exception as e:
                print(f"⚠️ Brain Router: Failed to initialize Grok: {e}")
                print("⚠️ Brain Router: Falling back to config-based messages")
                self.brain_type = "config"

        elif self.brain_type == "gemini":
            try:
                from brains.gemini_brain import GeminiBrain
                self.brain = GeminiBrain()
                print(f"✅ Brain Router: Using Gemini (model: {self.brain.model})")
            except Exception as e:
                print(f"⚠️ Brain Router: Failed to initialize Gemini: {e}")
                print("⚠️ Brain Router: Falling back to config-based messages")
                self.brain_type = "config"

        elif self.brain_type == "config":
            hybrid_status = " (hybrid mode enabled)" if self.use_hybrid else ""
            print(f"✅ Brain Router: Using config-based messages (no AI){hybrid_status}")
            self.brain = None

        else:
            print(f"⚠️ Brain Router: Unknown brain type '{self.brain_type}', using config")
            self.brain_type = "config"
            self.brain = None

    @staticmethod
    def _normalize_language(language: Optional[str]) -> str:
        """Normalize locale-like inputs to supported language codes."""
        value = (language or "en").strip().lower()
        if value.startswith(("nb", "nn", "no")):
            return "no"
        if value.startswith("da"):
            return "da"
        if value.startswith("en"):
            return "en"
        return "en"

    def _set_last_route_meta(self, **kwargs) -> None:
        meta = {
            "provider": "unknown",
            "source": "unknown",
            "status": "unknown",
            "mode": None,
            "timestamp": time.time(),
        }
        meta.update(kwargs)
        self.last_route_meta = meta

    def get_last_route_meta(self) -> Dict[str, Any]:
        """Get metadata for the most recent brain route decision."""
        return dict(self.last_route_meta)

    def _qa_timeout_for(self, brain_name: str, timeout_cap_seconds: Optional[float] = None) -> float:
        """
        Resolve timeout for ad-hoc question answering.

        Keeps Q&A snappy while allowing a bit more thinking time.
        """
        base_timeout = self._get_brain_timeout(brain_name, "chat")
        default_cap = float(getattr(config, "COACH_QA_TIMEOUT_SECONDS", 5.0))
        cap = default_cap
        if timeout_cap_seconds is not None:
            try:
                cap = max(0.8, float(timeout_cap_seconds))
            except Exception:
                cap = default_cap
        return max(0.8, min(base_timeout, cap))

    def _qa_max_tokens(self) -> int:
        try:
            return max(48, int(getattr(config, "COACH_QA_MAX_TOKENS", 110)))
        except Exception:
            return 110

    def _qa_max_sentences(self) -> int:
        try:
            return max(3, int(getattr(config, "COACH_QA_MAX_SENTENCES", 5)))
        except Exception:
            return 5

    def _build_qa_system_prompt(
        self,
        language: str,
        persona: Optional[str],
        context: str,
        user_name: Optional[str],
    ) -> str:
        persona_key = (persona or "personal_trainer").strip().lower()
        if persona_key not in {"personal_trainer", "toxic_mode"}:
            persona_key = "personal_trainer"
        mode_hint = "workout" if context == "workout" else "chat"
        name_hint = ""
        if user_name:
            name_hint = (
                f"- Athlete name: {user_name}. Use the name at most once, only if natural.\n"
            )

        if language == "no":
            return (
                "Du er en løpecoach som svarer kort og konkret på spørsmål.\n"
                "- Hold svaret så kort som mulig. Mål: 1-3 setninger.\n"
                f"- Du kan bruke opptil {self._qa_max_sentences()} setninger hvis det trengs for klarhet.\n"
                "- Forklar enkelt, uten lange avsnitt.\n"
                "- Hold svaret muntlig og naturlig på norsk.\n"
                "- Ikke finn opp medisinske fakta eller tall.\n"
                "- Svar kun på tema om trening, helse, kropp, restitusjon og ernæring.\n"
                "- Avvis seksualisert, trakasserende eller irrelevante tema kort og høflig.\n"
                f"- Persona: {persona_key} (tone påvirkes, ikke fakta).\n"
                f"- Context: {mode_hint}.\n"
                f"{name_hint}"
            )
        return (
            "You are a running coach answering athlete questions clearly.\n"
            "- Keep answers as short as possible. Target 1-3 sentences.\n"
            f"- You may use up to {self._qa_max_sentences()} sentences when needed for clarity.\n"
            "- Keep it practical, plain language, and spoken-friendly.\n"
            "- Do not invent medical facts or fake citations.\n"
            "- Only answer training/health/body/recovery/nutrition questions.\n"
            "- Refuse sexual, harassing, or unrelated topics briefly and politely.\n"
            f"- Persona: {persona_key} (tone only, not facts).\n"
            f"- Context: {mode_hint}.\n"
            f"{name_hint}"
        )

    def build_workout_talk_prompt(
        self,
        *,
        question: str,
        language: str,
        workout_context: Optional[dict],
    ) -> str:
        """
        Build deterministic workout context hints for Q&A prompts.
        This keeps /coach/talk grounded even without live HR.
        """
        context = workout_context if isinstance(workout_context, dict) else {}
        lang = self._normalize_language(language)
        parts = [f"Athlete question: {question.strip()}".strip()]
        hints = []

        phase = str(context.get("phase") or "").strip().lower()
        if phase:
            hints.append(f"phase={phase}")

        reps_left = context.get("reps_remaining_including_current")
        if isinstance(reps_left, (int, float)):
            hints.append(f"reps_remaining_including_current={int(reps_left)}")

        time_left = context.get("time_left_s")
        if isinstance(time_left, (int, float)):
            hints.append(f"time_left_s={max(0, int(time_left))}")

        hr = context.get("heart_rate")
        zone_state = str(context.get("zone_state") or "").strip().lower()
        hr_valid = isinstance(hr, (int, float)) and int(hr) > 0 and zone_state not in {"hr_missing", "targets_unenforced"}
        if hr_valid:
            hints.append(f"heart_rate={int(hr)}")
            low = context.get("target_hr_low")
            high = context.get("target_hr_high")
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                hints.append(f"target_hr_range={int(low)}-{int(high)}")
        else:
            hints.append("heart_rate=unavailable")

        profile_max = context.get("profile_max_hr_bpm")
        profile_rest = context.get("profile_resting_hr_bpm")
        profile_age = context.get("profile_age")
        if isinstance(profile_max, (int, float)):
            hints.append(f"profile_max_hr_bpm={int(profile_max)}")
        if isinstance(profile_rest, (int, float)):
            hints.append(f"profile_resting_hr_bpm={int(profile_rest)}")
        if isinstance(profile_age, (int, float)):
            hints.append(f"profile_age={int(profile_age)}")

        if hints:
            parts.append("Workout context: " + ", ".join(hints))
        if lang == "no":
            parts.append(
                "Instruksjon: Gi et kort, praktisk svar. Bruk reps/tid igjen når tilgjengelig. "
                "Ikke oppgi puls-tall når heart_rate=unavailable."
            )
        else:
            parts.append(
                "Instruction: Give a short practical answer. Use sets/time left when available. "
                "Do not state current HR numbers when heart_rate=unavailable."
            )
        return "\n".join(parts).strip()

    @staticmethod
    def _trim_to_sentence_limit(text: str, max_sentences: int = 5) -> str:
        cleaned = re.sub(r"\s+", " ", (text or "")).strip()
        if not cleaned:
            return ""
        if cleaned.lower().startswith("[error"):
            return ""

        parts = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", cleaned) if segment.strip()]
        if not parts:
            words = cleaned.split()
            clipped = " ".join(words[:45]).strip()
            if clipped and clipped[-1] not in ".!?":
                clipped += "."
            return clipped

        clipped_parts = parts[:max(1, int(max_sentences))]
        clipped = " ".join(clipped_parts).strip()
        if clipped and clipped[-1] not in ".!?":
            clipped += "."
        return clipped

    @staticmethod
    def _question_tokens(question: str) -> set:
        lowered = (question or "").lower()
        return set(re.findall(r"[a-z0-9æøå]+", lowered))

    def _classify_talk_policy_category(self, text: str) -> Optional[str]:
        tokens = self._question_tokens(text)
        lowered = (text or "").lower()

        if tokens.intersection(self._SEXUAL_EXPLICIT_TOKENS):
            return "sexual_explicit"

        if tokens.intersection(self._HARASSMENT_TOKENS):
            return "harassment_bullying"

        if (tokens.intersection(self._HATE_TOKENS) and tokens.intersection(self._PROTECTED_GROUP_TOKENS)) or (
            self._HATE_STRONG_TOKENS.intersection(tokens)
        ):
            return "hate_speech"

        if tokens.intersection(self._HARMFUL_TOKENS) or any(pattern in lowered for pattern in self._HARMFUL_PATTERNS):
            return "harmful_encouragement"

        if tokens.intersection(self._DOMAIN_TOKENS):
            return None

        return "off_topic"

    def _is_workout_context_prompt(self, text: str) -> bool:
        lowered = (text or "").strip().lower()
        if not lowered:
            return False
        if lowered in self._WORKOUT_CONTEXT_PROMPT_EXACT:
            return True
        return any(lowered.startswith(prefix) for prefix in self._WORKOUT_CONTEXT_PROMPT_PREFIXES)

    def _next_talk_policy_refusal(self, language: str, category: str) -> tuple[str, str]:
        normalized_language = self._normalize_language(language)
        bank = getattr(config, "COACH_TALK_POLICY_REFUSAL_BANK", {}) or {}
        phrases = bank.get(normalized_language) or bank.get("en") or [
            "Lets talk about your workout instead"
        ]

        if not phrases:
            return "Lets talk about your workout instead", f"talk_policy.{normalized_language}.{category}.1"

        idx_key = (normalized_language, category)
        rotate_enabled = bool(getattr(config, "COACH_TALK_POLICY_ROTATE_ENABLED", True))
        if rotate_enabled and len(phrases) > 1:
            last_idx = int(self._talk_policy_rotation_state.get(idx_key, -1))
            idx = (last_idx + 1) % len(phrases)
            self._talk_policy_rotation_state[idx_key] = idx
        else:
            idx = 0
            self._talk_policy_rotation_state[idx_key] = idx

        return phrases[idx], f"talk_policy.{normalized_language}.{category}.{idx + 1}"

    def evaluate_talk_policy(self, message: str, language: str, talk_context: str = "chat") -> Dict[str, Any]:
        strict_enabled = bool(getattr(config, "COACH_TALK_STRICT_SAFETY_ENABLED", True))
        if not strict_enabled:
            return {
                "policy_blocked": False,
                "policy_category": None,
                "policy_phrase_id": None,
                "policy_reason": None,
                "policy_status": None,
                "text": "",
            }

        normalized_context = (talk_context or "chat").strip().lower()
        category = self._classify_talk_policy_category(message or "")
        if category == "off_topic" and normalized_context == "workout" and self._is_workout_context_prompt(message):
            category = None

        if not category:
            return {
                "policy_blocked": False,
                "policy_category": None,
                "policy_phrase_id": None,
                "policy_reason": None,
                "policy_status": None,
                "text": "",
            }

        normalized_language = self._normalize_language(language)
        text, phrase_id = self._next_talk_policy_refusal(normalized_language, category)
        status_map = {
            "off_topic": "policy_refusal_off_topic",
            "sexual_explicit": "policy_refusal_disallowed_topic",
            "harassment_bullying": "policy_refusal_disallowed_topic",
            "hate_speech": "policy_refusal_hate_speech",
            "harmful_encouragement": "policy_refusal_harmful_encouragement",
        }
        reason_map = {
            "off_topic": "Lets talk about workout-relevant topics.",
            "sexual_explicit": "Sexual or explicit content is disallowed.",
            "harassment_bullying": "Harassment and bullying content is disallowed.",
            "hate_speech": "Hate speech content is disallowed.",
            "harmful_encouragement": "Unsafe and harmful encouragement is disallowed.",
        }
        print(
            f"🛡️ TALK_POLICY category={category} blocked=true "
            f"lang={normalized_language} context={normalized_context}"
        )
        return {
            "policy_blocked": True,
            "policy_category": category,
            "policy_phrase_id": phrase_id,
            "policy_reason": reason_map.get(category),
            "policy_status": status_map.get(category, "policy_refusal"),
            "text": text,
        }

    def _qa_policy_response(self, question: str, language: str, context: str = "chat") -> tuple[str, Optional[str]]:
        policy = self.evaluate_talk_policy(question, language, talk_context=context)
        if not policy.get("policy_blocked"):
            return "", None
        return str(policy.get("text") or ""), str(policy.get("policy_status") or "policy_refusal")

    def _qa_fallback(self, language: str) -> str:
        if language == "no":
            return (
                "Trening gir bedre kondisjon, sterkere hjerte og mer energi i hverdagen. "
                "Start rolig og vær jevn over tid. "
                "Små økter ofte gir bedre resultat enn sjeldne skippertak."
            )
        return (
            "Training improves endurance, heart health, and day-to-day energy. "
            "Start easy and stay consistent. "
            "Small sessions done often beat occasional all-out efforts."
        )

    def _answer_question_with_brain(
        self,
        brain: Any,
        *,
        question: str,
        language: str,
        persona: Optional[str],
        context: str,
        user_name: Optional[str],
        timeout: float,
    ) -> str:
        if not hasattr(brain, "chat"):
            return ""

        system_prompt = self._build_qa_system_prompt(
            language=language,
            persona=persona,
            context=context,
            user_name=user_name,
        )
        response = asyncio.run(
            brain.chat(
                messages=[{"role": "user", "content": question}],
                system_prompt=system_prompt,
                temperature=0.25,
                max_tokens=self._qa_max_tokens(),
                timeout=max(0.8, float(timeout) - 0.2),
            )
        )
        return self._trim_to_sentence_limit(response, max_sentences=self._qa_max_sentences())

    def get_question_response(
        self,
        question: str,
        *,
        language: str = "en",
        persona: Optional[str] = None,
        context: str = "chat",
        user_name: Optional[str] = None,
        timeout_cap_seconds: Optional[float] = None,
    ) -> str:
        """
        Answer a direct user question with fast, concise output.

        Priority for this path is Grok first (when available), then other AI brains.
        """
        prompt = (question or "").strip()
        lang = self._normalize_language(language)
        if not prompt:
            fallback = self._qa_fallback(lang)
            self._set_last_route_meta(
                provider="config",
                source="config_fallback",
                status="empty_question_fallback",
                mode="question_qa",
            )
            return fallback

        policy_reply, policy_status = self._qa_policy_response(prompt, lang, context=context)
        if policy_reply:
            self._set_last_route_meta(
                provider="policy",
                source="domain_guard",
                status=policy_status or "policy_refusal",
                mode="question_qa",
            )
            return policy_reply.strip()

        attempted = []
        candidate_brains = ["grok"]

        if self.use_priority_routing and self.priority_brains:
            for brain_name in self.priority_brains:
                if brain_name in {"grok", "config"}:
                    continue
                if brain_name not in candidate_brains:
                    candidate_brains.append(brain_name)
        elif self.brain_type not in {"priority", "config", "grok"}:
            candidate_brains.append(self.brain_type)

        for brain_name in candidate_brains:
            if not self._is_brain_available(brain_name):
                reason = self._get_skip_reason(brain_name)
                attempted.append({"brain": brain_name, "status": "skipped", "reason": reason})
                continue

            brain = self._get_brain_instance(brain_name)
            if brain is None:
                attempted.append({"brain": brain_name, "status": "unavailable"})
                continue

            timeout = self._qa_timeout_for(brain_name, timeout_cap_seconds=timeout_cap_seconds)
            fn = lambda brain=brain, timeout=timeout: self._answer_question_with_brain(
                brain,
                question=prompt,
                language=lang,
                persona=persona,
                context=context,
                user_name=user_name,
                timeout=timeout,
            )
            result = self._call_brain_with_timeout(brain_name, fn, timeout)
            result = self._trim_to_sentence_limit(result, max_sentences=self._qa_max_sentences())

            if result:
                attempted.append({"brain": brain_name, "status": "success"})
                self._set_last_route_meta(
                    provider=brain_name,
                    source="ai_qna",
                    status="success",
                    mode="question_qa",
                    timeout=timeout,
                    attempted=attempted,
                )
                return result

            outcome = dict(self.brain_last_outcome.get(brain_name, {}))
            attempted.append(
                {
                    "brain": brain_name,
                    "status": outcome.get("status", "empty_response"),
                    "timeout": timeout,
                }
            )

        fallback = self._qa_fallback(lang)
        self._set_last_route_meta(
            provider="config",
            source="config_fallback",
            status="all_question_brains_failed_or_skipped",
            mode="question_qa",
            attempted=attempted,
        )
        return fallback

    @staticmethod
    def _normalize_repeat_key(text: str) -> str:
        """Normalize text for repetition checks."""
        return " ".join((text or "").strip().lower().split())

    def _recent_output_window(self) -> int:
        try:
            return max(1, int(getattr(config, "BRAIN_RECENT_CUE_WINDOW", 4)))
        except Exception:
            return 4

    def _get_recent_outputs(self, session_id: Optional[str]) -> list:
        if not session_id:
            return []
        return list(self._recent_outputs_by_session.get(session_id, []))

    def _record_recent_output(self, session_id: Optional[str], text: str) -> None:
        if not session_id:
            return
        cleaned = (text or "").strip()
        if not cleaned:
            return
        bucket = self._recent_outputs_by_session.setdefault(session_id, [])
        bucket.append(cleaned)
        window = self._recent_output_window()
        if len(bucket) > window:
            del bucket[:-window]

    def _rewrite_if_recent_repeat(
        self,
        text: str,
        session_id: Optional[str],
        breath_data: Dict[str, Any],
        phase: str,
        language: str,
        persona: Optional[str],
    ) -> str:
        """
        Avoid exact cue repeats for the same session.

        If provider output repeats a recent cue, use a config cue fallback
        that differs from recent outputs when possible.
        """
        if not session_id:
            return text

        normalized = self._normalize_repeat_key(text)
        recent_norm = {self._normalize_repeat_key(item) for item in self._get_recent_outputs(session_id)}
        if normalized not in recent_norm:
            return text

        replacement = text
        for _ in range(4):
            candidate = self._get_config_response(breath_data, phase, language=language, persona=persona)
            candidate_norm = self._normalize_repeat_key(candidate)
            if candidate_norm != normalized and candidate_norm not in recent_norm:
                replacement = candidate
                break

        if self._normalize_repeat_key(replacement) != normalized:
            meta = dict(self.last_route_meta)
            meta["status"] = "anti_repeat_rewrite"
            meta["source"] = f"{meta.get('source', 'ai')}_anti_repeat"
            meta["timestamp"] = time.time()
            self.last_route_meta = meta

        return replacement

    def _create_brain(self, brain_name: str):
        """Create a brain instance by name."""
        if brain_name == "claude":
            from brains.claude_brain import ClaudeBrain
            return ClaudeBrain()
        if brain_name == "openai":
            from brains.openai_brain import OpenAIBrain
            return OpenAIBrain()
        if brain_name == "grok":
            from brains.grok_brain import GrokBrain
            return GrokBrain()
        if brain_name == "gemini":
            from brains.gemini_brain import GeminiBrain
            return GeminiBrain()
        if brain_name == "config":
            return None
        raise ValueError(f"Unknown brain type: {brain_name}")

    def _get_brain_instance(self, brain_name: str):
        """Get or lazily initialize a brain instance."""
        if brain_name in self.brain_pool:
            cached = self.brain_pool[brain_name]
            if cached is not None:
                return cached
            # Cached failure — retry if cooldown expired
            cooldown_until = self.brain_cooldowns.get(brain_name, 0)
            if time.time() < cooldown_until:
                return None  # Still in cooldown
            # Cooldown expired — clear cache and retry below
            del self.brain_pool[brain_name]
        try:
            brain = self._create_brain(brain_name)
            self.brain_pool[brain_name] = brain
            if brain is not None:
                print(f"✅ Brain Router: Loaded {brain_name} (model: {brain.model})")
            return brain
        except Exception as e:
            print(f"⚠️ Brain Router: Failed to initialize {brain_name}: {e}")
            # Use short init-retry cooldown (not the 60s runtime cooldown)
            init_retry = getattr(config, "BRAIN_INIT_RETRY_SECONDS", 5)
            self._set_cooldown(brain_name, seconds=init_retry)
            self.brain_pool[brain_name] = None
            return None

    def _set_cooldown(self, brain_name: str, seconds: Optional[float] = None):
        cooldown = seconds if seconds is not None else getattr(config, "BRAIN_COOLDOWN_SECONDS", 60)
        self.brain_cooldowns[brain_name] = time.time() + cooldown

    def _is_brain_available(self, brain_name: str) -> bool:
        self._prune_expired_cooldowns()
        cooldown_until = self.brain_cooldowns.get(brain_name)
        if cooldown_until and time.time() < cooldown_until:
            return False

        usage = getattr(config, "BRAIN_USAGE", {}).get(brain_name, 0.0)
        usage_limit = getattr(config, "USAGE_LIMIT", 0.9)
        if usage >= usage_limit:
            return False

        stats = self.brain_stats.get(brain_name, {})
        avg_latency = stats.get("avg_latency")
        slow_threshold = self._get_slow_threshold(brain_name)
        if slow_threshold and avg_latency and avg_latency > slow_threshold:
            return False

        return True

    def _get_brain_timeout(self, brain_name: str, mode: str) -> float:
        """
        Resolve timeout for a given brain/mode.

        Priority:
        1) BRAIN_MODE_TIMEOUTS[mode][brain_name]
        2) BRAIN_MODE_TIMEOUTS[mode]["default"]
        3) BRAIN_TIMEOUTS[brain_name]
        4) BRAIN_TIMEOUT (global default)
        """
        mode_timeouts = getattr(config, "BRAIN_MODE_TIMEOUTS", {}) or {}
        if isinstance(mode_timeouts, dict):
            per_mode = mode_timeouts.get(mode, {})
            if isinstance(per_mode, dict):
                if brain_name in per_mode:
                    return float(per_mode[brain_name])
                if "default" in per_mode:
                    return float(per_mode["default"])

        per_brain_timeouts = getattr(config, "BRAIN_TIMEOUTS", {}) or {}
        if isinstance(per_brain_timeouts, dict) and brain_name in per_brain_timeouts:
            return float(per_brain_timeouts[brain_name])

        return float(getattr(config, "BRAIN_TIMEOUT", 1.2))

    def _get_slow_threshold(self, brain_name: str) -> Optional[float]:
        """Resolve slow-threshold with optional per-brain override."""
        per_brain_thresholds = getattr(config, "BRAIN_SLOW_THRESHOLDS", {}) or {}
        if isinstance(per_brain_thresholds, dict) and brain_name in per_brain_thresholds:
            return float(per_brain_thresholds[brain_name])
        threshold = getattr(config, "BRAIN_SLOW_THRESHOLD", None)
        return float(threshold) if threshold is not None else None

    def _get_skip_reason(self, brain_name: str) -> str:
        """Return a human-readable reason why this brain is unavailable."""
        self._prune_expired_cooldowns()
        cooldown_until = self.brain_cooldowns.get(brain_name)
        if cooldown_until and time.time() < cooldown_until:
            remaining = cooldown_until - time.time()
            # Distinguish init failure from runtime cooldown
            if brain_name in self.brain_pool and self.brain_pool[brain_name] is None:
                return f"init_failed (retry in {remaining:.0f}s)"
            outcome = self.brain_last_outcome.get(brain_name, {})
            if outcome.get("status") == "quota_limited":
                return f"quota_cooldown ({remaining:.0f}s remaining)"
            return f"cooldown ({remaining:.0f}s remaining)"

        usage = getattr(config, "BRAIN_USAGE", {}).get(brain_name, 0.0)
        usage_limit = getattr(config, "USAGE_LIMIT", 0.9)
        if usage >= usage_limit:
            return f"usage_limit ({usage:.0%} >= {usage_limit:.0%})"

        stats = self.brain_stats.get(brain_name, {})
        avg_latency = stats.get("avg_latency")
        slow_threshold = self._get_slow_threshold(brain_name)
        if slow_threshold and avg_latency and avg_latency > slow_threshold:
            return f"too_slow (avg {avg_latency:.3f}s > {slow_threshold}s)"

        return "unknown"

    def _record_latency(self, brain_name: str, latency: float):
        stats = self.brain_stats.setdefault(brain_name, {"calls": 0, "avg_latency": 0.0, "timeouts": 0, "failures": 0, "last_used": None})
        stats["calls"] += 1
        stats["last_used"] = time.time()
        # Exponential moving average — decays old values so a single timeout doesn't permanently disable a brain
        decay = getattr(config, "BRAIN_LATENCY_DECAY_FACTOR", 0.9)
        stats["avg_latency"] = (stats["avg_latency"] * decay) + (latency * (1 - decay))

    def _record_failure(self, brain_name: str, cooldown_seconds: Optional[float] = None):
        stats = self.brain_stats.setdefault(brain_name, {"calls": 0, "avg_latency": 0.0, "timeouts": 0, "failures": 0})
        stats["failures"] += 1
        self._set_cooldown(brain_name, seconds=cooldown_seconds)

    def _get_failure_cooldown_seconds(self, brain_name: str, error: Exception) -> Optional[float]:
        """
        Return provider-aware cooldown override for known transient failures.

        Gemini free-tier quota errors should cool down longer to avoid repeated
        retries every tick.
        """
        if brain_name != "gemini":
            return None

        message = str(error or "")
        lower = message.lower()
        quota_markers = (
            "quota",
            "resource_exhausted",
            "generativelanguage.googleapis.com",
            "429",
            "retry_delay",
        )
        if not any(marker in lower for marker in quota_markers):
            return None

        quota_cooldown = float(getattr(config, "BRAIN_QUOTA_COOLDOWN_SECONDS", 300))
        parsed_retry = None

        match = re.search(r"retry_delay.*?seconds\s*[:=]\s*(\d+)", message, flags=re.IGNORECASE | re.DOTALL)
        if match:
            parsed_retry = float(match.group(1))
        else:
            match = re.search(r"seconds\s*[:=]\s*(\d+)", message, flags=re.IGNORECASE)
            if match:
                parsed_retry = float(match.group(1))

        if parsed_retry is not None:
            return max(quota_cooldown, parsed_retry + 5.0)

        return quota_cooldown

    def _record_timeout(self, brain_name: str):
        stats = self.brain_stats.setdefault(brain_name, {"calls": 0, "avg_latency": 0.0, "timeouts": 0, "failures": 0})
        stats["timeouts"] += 1
        self._set_cooldown(brain_name, seconds=getattr(config, "BRAIN_TIMEOUT_COOLDOWN_SECONDS", 30))

    def _call_brain_with_timeout(self, brain_name: str, fn, timeout: float):
        start = time.time()
        future = self._executor.submit(fn)
        try:
            result = future.result(timeout=timeout)
            latency = time.time() - start
            self._record_latency(brain_name, latency)
            self.brain_last_outcome[brain_name] = {
                "status": "success" if result else "empty",
                "latency": latency,
                "timeout": timeout,
            }
            success = bool(result)
            print(f"[BRAIN] {brain_name} | latency={latency:.3f}s | success={success}")
            return result
        except TimeoutError:
            latency = time.time() - start
            cancelled = future.cancel()  # Best-effort; returns False if already running
            self._record_timeout(brain_name)
            self.brain_last_outcome[brain_name] = {
                "status": "timeout",
                "latency": latency,
                "timeout": timeout,
                "cancelled": cancelled,
            }
            print(f"[BRAIN] {brain_name} | TIMEOUT after {latency:.3f}s | cancelled={cancelled}")
            return None
        except Exception as e:
            latency = time.time() - start
            failure_cooldown = self._get_failure_cooldown_seconds(brain_name, e)
            self._record_failure(brain_name, cooldown_seconds=failure_cooldown)
            failure_status = "quota_limited" if failure_cooldown is not None else "failure"
            self.brain_last_outcome[brain_name] = {
                "status": failure_status,
                "latency": latency,
                "timeout": timeout,
                "error": f"{type(e).__name__}: {e}",
                "cooldown_seconds": failure_cooldown,
            }
            print(f"[BRAIN] {brain_name} | FAILURE after {latency:.3f}s | {type(e).__name__}: {e}")
            return None

    def _get_priority_response(
        self,
        breath_data: Dict[str, Any],
        phase: str,
        mode: str,
        language: str,
        persona: Optional[str]
    ) -> str:
        attempted = []
        for brain_name in self.priority_brains:
            if not self._is_brain_available(brain_name):
                reason = self._get_skip_reason(brain_name)
                print(f"[BRAIN] {brain_name} | SKIPPED | {reason}")
                attempted.append({"brain": brain_name, "status": "skipped", "reason": reason})
                continue

            if brain_name == "config":
                self._set_last_route_meta(
                    provider="config",
                    source="config",
                    status="config_selected",
                    mode=mode,
                    attempted=attempted + [{"brain": "config", "status": "selected"}],
                )
                return self._get_config_response(breath_data, phase, language=language, persona=persona)

            brain = self._get_brain_instance(brain_name)
            if brain is None:
                attempted.append({"brain": brain_name, "status": "unavailable"})
                continue

            if mode == "realtime_coach":
                fn = lambda: brain.get_realtime_coaching(breath_data, phase)
            else:
                fn = lambda: brain.get_coaching_response(breath_data, phase)

            timeout = self._get_brain_timeout(brain_name, mode)
            result = self._call_brain_with_timeout(brain_name, fn, timeout)
            if result:
                attempted.append({"brain": brain_name, "status": "success"})
                self._set_last_route_meta(
                    provider=brain_name,
                    source="ai",
                    status="success",
                    mode=mode,
                    timeout=timeout,
                    attempted=attempted,
                )
                return result
            outcome = dict(self.brain_last_outcome.get(brain_name, {}))
            attempted.append(
                {
                    "brain": brain_name,
                    "status": outcome.get("status", "failed"),
                    "timeout": timeout,
                }
            )

        self._set_last_route_meta(
            provider="config",
            source="config_fallback",
            status="all_brains_failed_or_skipped",
            mode=mode,
            attempted=attempted,
        )
        return self._get_config_response(breath_data, phase, language=language, persona=persona)

    def _initialize_hybrid_claude(self):
        """
        STEP 4: Initialize Claude brain for hybrid mode pattern detection.

        This allows config brain to handle fast responses, while Claude provides
        intelligent pattern detection and trend analysis in the background.
        """
        try:
            from brains.claude_brain import ClaudeBrain
            self.claude_brain = ClaudeBrain()
            print(f"✅ Brain Router: Hybrid mode - Claude available for patterns (model: {self.claude_brain.model})")
        except Exception as e:
            print(f"⚠️ Brain Router: Hybrid mode - Claude unavailable: {e}")
            print("   Continuing with config-only mode")
            self.claude_brain = None

    def get_coaching_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense",
        mode: str = "realtime_coach",
        language: str = "en",
        persona: str = None,
        user_name: str = None
    ) -> str:
        """
        Get coaching response from active brain.

        This is the main API method that the app calls.

        Args:
            breath_data: Dictionary containing breath analysis metrics
            phase: Current workout phase ("warmup", "intense", "cooldown")
            mode: Brain mode - "chat" or "realtime_coach" (default: realtime_coach)
            language: "en" or "no" for language-specific message selection
            persona: Optional persona override (e.g. "toxic_mode" for toxic message bank)
            user_name: Optional user name for personalized coaching (e.g. "Marius")

        Returns:
            String containing coaching message
        """
        language = self._normalize_language(language)

        # Inject language + user_name into breath_data for AI brains
        local_breath_data = dict(breath_data or {})
        local_breath_data["language"] = language
        if persona:
            local_breath_data["persona"] = persona
        if user_name:
            local_breath_data["user_name"] = user_name
        if self.use_priority_routing and self.priority_brains:
            result = self._get_priority_response(local_breath_data, phase, mode, language, persona)
            if mode == "realtime_coach":
                session_id = local_breath_data.get("session_id")
                result = self._rewrite_if_recent_repeat(
                    text=result,
                    session_id=session_id,
                    breath_data=local_breath_data,
                    phase=phase,
                    language=language,
                    persona=persona,
                )
                self._record_recent_output(session_id, result)
            return result
        # STEP 3: Route to appropriate brain mode
        if mode == "realtime_coach":
            # Use optimized real-time coach brain (fast, actionable, no explanations)
            if self.brain is not None:
                try:
                    result = self.brain.get_realtime_coaching(local_breath_data, phase)
                    session_id = local_breath_data.get("session_id")
                    result = self._rewrite_if_recent_repeat(
                        text=result,
                        session_id=session_id,
                        breath_data=local_breath_data,
                        phase=phase,
                        language=language,
                        persona=persona,
                    )
                    self._record_recent_output(session_id, result)
                    self._set_last_route_meta(
                        provider=self.get_active_brain(),
                        source="ai",
                        status="success",
                        mode=mode,
                    )
                    return result
                except Exception as e:
                    print(f"⚠️ Brain Router: Real-time brain error: {e}, using fallback")
                    self._set_last_route_meta(
                        provider="config",
                        source="config_fallback",
                        status="exception_fallback",
                        mode=mode,
                        error=f"{type(e).__name__}: {e}",
                    )
                    return self._get_config_response(breath_data, phase, language=language, persona=persona)
            else:
                # Config mode uses same messages for both modes
                self._set_last_route_meta(
                    provider="config",
                    source="config",
                    status="config_mode",
                    mode=mode,
                )
                return self._get_config_response(breath_data, phase, language=language, persona=persona)

        elif mode == "chat":
            # Use conversational chat brain (explanatory, educational)
            if self.brain is not None:
                try:
                    result = self.brain.get_coaching_response(local_breath_data, phase)
                    self._record_recent_output(local_breath_data.get("session_id"), result)
                    self._set_last_route_meta(
                        provider=self.get_active_brain(),
                        source="ai",
                        status="success",
                        mode=mode,
                    )
                    return result
                except Exception as e:
                    print(f"⚠️ Brain Router: Chat brain error: {e}, using fallback")
                    self._set_last_route_meta(
                        provider="config",
                        source="config_fallback",
                        status="exception_fallback",
                        mode=mode,
                        error=f"{type(e).__name__}: {e}",
                    )
                    return self._get_config_response(breath_data, phase, language=language, persona=persona)
            else:
                self._set_last_route_meta(
                    provider="config",
                    source="config",
                    status="config_mode",
                    mode=mode,
                )
                return self._get_config_response(breath_data, phase, language=language, persona=persona)

        else:
            print(f"⚠️ Brain Router: Unknown mode '{mode}', using realtime_coach")
            return self.get_coaching_response(breath_data, phase, mode="realtime_coach", language=language, persona=persona)

    def _get_config_response(
        self,
        breath_data: Dict[str, Any],
        phase: str = "intense",
        language: str = "en",
        persona: str = None
    ) -> str:
        """
        Get response from config messages (no AI).
        Supports language selection (EN/NO) and persona-specific message banks.
        """
        intensity = breath_data.get("intensity", breath_data.get("intensitet", "moderate"))

        # Route to toxic mode message bank if persona is toxic_mode
        if persona == "toxic_mode":
            return self._get_toxic_response(intensity, phase, language)

        # Select message bank based on language
        if language == "no":
            messages = config.CONTINUOUS_COACH_MESSAGES_NO
        else:
            messages = config.CONTINUOUS_COACH_MESSAGES

        # Critical override
        if intensity in ("critical", "kritisk"):
            return random.choice(messages.get("critical", ["Stop! Breathe."]))

        # Phase-based responses
        if phase == "warmup":
            return random.choice(messages.get("warmup", ["Easy pace."]))

        if phase == "cooldown":
            return random.choice(messages.get("cooldown", ["Slow down."]))

        # Intense phase with intensity levels
        if phase == "intense":
            intense_msgs = messages.get("intense", {})
            # Normalize intensity key
            intensity_key = intensity if intensity in intense_msgs else "moderate"
            if intensity_key in intense_msgs:
                return random.choice(intense_msgs[intensity_key])

        return "Fortsett!" if language == "no" else "Keep going!"

    def _get_toxic_response(
        self,
        intensity: str,
        phase: str,
        language: str = "en"
    ) -> str:
        """Get response from toxic mode message bank."""
        language = self._normalize_language(language)
        lang_key = language if language in config.TOXIC_MODE_MESSAGES else "en"
        messages = config.TOXIC_MODE_MESSAGES[lang_key]

        # Critical override (safety first, even in toxic mode)
        if intensity in ("critical", "kritisk"):
            return random.choice(messages.get("critical", ["Stop. Breathe. Safety first."]))

        # Phase-based responses
        if phase == "warmup":
            return random.choice(messages.get("warmup", ["MOVE!"]))

        if phase == "cooldown":
            return random.choice(messages.get("cooldown", ["Fine. Rest."]))

        # Intense phase
        if phase == "intense":
            intense_msgs = messages.get("intense", {})
            intensity_key = intensity if intensity in intense_msgs else "moderate"
            if intensity_key in intense_msgs:
                return random.choice(intense_msgs[intensity_key])

        return "KEEP GOING!" if language != "no" else "FORTSETT!"

    def get_active_brain(self) -> str:
        """Get the name of the currently active brain."""
        if self.brain_type == "priority":
            return "priority"
        if self.brain is not None:
            return self.brain.get_provider_name()
        return "config"

    def get_brain_stats(self) -> Dict[str, Any]:
        """Get per-brain call statistics for observability."""
        self._prune_expired_cooldowns()
        stats = {}
        for brain_name in (self.priority_brains or [self.brain_type]):
            s = self.brain_stats.get(brain_name, {})
            cooldown_until = self.brain_cooldowns.get(brain_name)
            on_cooldown = bool(cooldown_until and time.time() < cooldown_until)
            stats[brain_name] = {
                "calls": s.get("calls", 0),
                "timeouts": s.get("timeouts", 0),
                "failures": s.get("failures", 0),
                "avg_latency": round(s.get("avg_latency", 0), 3),
                "last_used": s.get("last_used"),
                "on_cooldown": on_cooldown,
                "available": self._is_brain_available(brain_name),
            }
        return stats

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of active brain.

        Returns:
            Dictionary with health status
        """
        self._prune_expired_cooldowns()
        # Build pool_status: which brains are cached and their state
        pool_status = {}
        for brain_name in self.brain_pool:
            if self.brain_pool[brain_name] is None:
                pool_status[brain_name] = "failed_init"
            else:
                pool_status[brain_name] = "ready"

        status = {
            "active_brain": self.get_active_brain(),
            "healthy": True,
            "message": "OK",
            "brain_stats": self.get_brain_stats(),
            "pool_status": pool_status
        }

        if self.brain is not None:
            try:
                brain_healthy = self.brain.health_check()
                status["healthy"] = brain_healthy
                if not brain_healthy:
                    status["message"] = "Brain health check failed"
            except Exception as e:
                status["healthy"] = False
                status["message"] = str(e)

        return status

    def get_fast_fallback_response(
        self,
        breath_data: Dict[str, Any],
        phase: str,
        language: str = "en",
        persona: str = None
    ) -> str:
        """Return a fast config cue when latency strategy chooses immediate fallback."""
        normalized_language = self._normalize_language(language)
        text = self._get_config_response(
            breath_data=breath_data,
            phase=phase,
            language=normalized_language,
            persona=persona,
        )
        self._set_last_route_meta(
            provider="system",
            source="latency_fast_fallback",
            status="fast_fallback",
            mode="realtime_coach",
        )
        return text

    def rewrite_zone_event_text(
        self,
        base_text: str,
        *,
        language: str = "en",
        persona: Optional[str] = None,
        coaching_style: str = "normal",
        event_type: Optional[str] = None,
    ) -> str:
        """
        Optional Phase-4 language layer for deterministic zone events.

        The event motor still owns decisioning/cooldowns/scoring; this method
        can only rewrite wording and always falls back to the deterministic
        template text.
        """
        seed = (base_text or "").strip()
        if not seed:
            return seed

        language = self._normalize_language(language)
        timeout_cap = float(getattr(config, "ZONE_EVENT_LLM_REWRITE_TIMEOUT_SECONDS", 0.9))
        attempted = []

        if self.use_priority_routing and self.priority_brains:
            candidate_brains = [name for name in self.priority_brains if name != "config"]
        else:
            active = self.get_active_brain()
            candidate_brains = [] if active in {"config", "priority"} else [active]

        for brain_name in candidate_brains:
            if not self._is_brain_available(brain_name):
                attempted.append({"brain": brain_name, "status": "skipped", "reason": self._get_skip_reason(brain_name)})
                continue

            if brain_name == self.get_active_brain() and self.brain is not None:
                brain = self.brain
            else:
                brain = self._get_brain_instance(brain_name)

            if brain is None:
                attempted.append({"brain": brain_name, "status": "unavailable"})
                continue

            timeout = min(timeout_cap, self._get_brain_timeout(brain_name, "realtime_coach"))
            fn = lambda: brain.rewrite_zone_event_text(
                seed,
                language=language,
                persona=persona,
                coaching_style=coaching_style,
                event_type=event_type,
            )
            rewritten = self._call_brain_with_timeout(brain_name, fn, timeout)
            cleaned = (rewritten or "").strip()
            if cleaned:
                attempted.append({"brain": brain_name, "status": "success", "timeout": timeout})
                self._set_last_route_meta(
                    provider=brain_name,
                    source="zone_event_llm",
                    status="rewrite_success",
                    mode="deterministic_zone",
                    timeout=timeout,
                    event_type=event_type,
                    attempted=attempted,
                )
                return cleaned

            outcome = dict(self.brain_last_outcome.get(brain_name, {}))
            attempted.append(
                {
                    "brain": brain_name,
                    "status": outcome.get("status", "failed"),
                    "timeout": timeout,
                }
            )

        self._set_last_route_meta(
            provider="system",
            source="zone_event_motor",
            status="rewrite_fallback",
            mode="deterministic_zone",
            event_type=event_type,
            attempted=attempted,
        )
        return seed

    def get_latency_fallback_signal(self, mode: str = "realtime_coach") -> Dict[str, Any]:
        """
        Estimate if a fast fallback should be used based on observed provider latency.

        Uses per-provider EMA latency statistics from priority routing.
        """
        enabled = bool(getattr(config, "LATENCY_FAST_FALLBACK_ENABLED", True))
        threshold = float(getattr(config, "LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS", 2.8))
        min_calls = int(getattr(config, "LATENCY_FAST_FALLBACK_MIN_CALLS", 2))

        base = {
            "should_fallback": False,
            "provider": None,
            "avg_latency": 0.0,
            "threshold": threshold,
            "calls": 0,
            "reason": "unknown",
            "mode": mode,
        }

        if not enabled:
            base["reason"] = "disabled"
            return base

        if self.use_priority_routing and self.priority_brains:
            order = [name for name in self.priority_brains if name != "config"]
        else:
            active = self.get_active_brain()
            order = [] if active in {"config", "priority"} else [active]

        if not order:
            base["reason"] = "no_ai_provider"
            return base

        stats = self.get_brain_stats()
        selected = None
        for provider in order:
            provider_stats = stats.get(provider, {})
            if not provider_stats:
                continue
            if not provider_stats.get("available", True):
                continue
            selected = (provider, provider_stats)
            break

        if selected is None:
            # Use first candidate even if currently unavailable (best effort signal).
            provider = order[0]
            selected = (provider, stats.get(provider, {}))

        provider, provider_stats = selected
        calls = int(provider_stats.get("calls", 0) or 0)
        avg_latency = float(provider_stats.get("avg_latency", 0.0) or 0.0)

        base.update({
            "provider": provider,
            "avg_latency": avg_latency,
            "calls": calls,
        })

        if calls < min_calls:
            base["reason"] = "insufficient_samples"
            return base

        if avg_latency >= threshold:
            base["should_fallback"] = True
            base["reason"] = "latency_high"
        else:
            base["reason"] = "latency_ok"

        return base

    def switch_brain(self, new_brain_type: str, preserve_hybrid: bool = True) -> bool:
        """
        STEP 4: Hot-switch to a different brain at runtime.

        Args:
            new_brain_type: "priority", "claude", "openai", "grok", "gemini", or "config"
            preserve_hybrid: Keep hybrid Claude brain if switching away from it

        Returns:
            True if switch successful, False otherwise
        """
        old_brain = self.brain_type
        if new_brain_type == "priority":
            self.use_priority_routing = True
            self.priority_brains = list(getattr(config, "BRAIN_PRIORITY", []))
            self.brain_type = "priority"
            self.brain = None
        else:
            self.use_priority_routing = False
            self.priority_brains = []
            self.brain_type = new_brain_type

        # STEP 4: Preserve hybrid Claude if requested
        if preserve_hybrid and self.claude_brain is not None:
            old_claude = self.claude_brain
        else:
            old_claude = None

        self._initialize_brain()

        # Restore hybrid Claude if preserved
        if preserve_hybrid and old_claude is not None:
            self.claude_brain = old_claude
            print(f"   Hybrid Claude brain preserved for pattern detection")

        success = (self.brain_type == new_brain_type)
        if success:
            print(f"✅ Brain Router: Switched from {old_brain} to {new_brain_type}")
        else:
            print(f"⚠️ Brain Router: Failed to switch to {new_brain_type}, stayed on {self.brain_type}")

        return success

    # ============================================
    # STEP 4: HYBRID MODE METHODS
    # ============================================

    def detect_pattern(
        self,
        breath_history: list,
        coaching_history: list,
        phase: str
    ) -> Optional[str]:
        """
        STEP 4: Use Claude to detect patterns and trends over time.

        This is called in the background (non-blocking) to provide higher-level
        encouragement based on workout progression.

        Args:
            breath_history: List of recent breath analyses
            coaching_history: List of recent coaching messages
            phase: Current workout phase

        Returns:
            Pattern insight string or None if no pattern detected
        """
        # Only works in hybrid mode with Claude available
        if not self.use_hybrid or self.claude_brain is None:
            return None

        # Need sufficient history to detect patterns
        if len(breath_history) < 3:
            return None

        try:
            # Build context for Claude
            context = self._build_pattern_context(breath_history, coaching_history, phase)

            # Ask Claude to detect patterns (using chat mode, not realtime)
            # This is intentionally slower/deeper than realtime coaching
            pattern_prompt = f"""Analyze this workout progression and identify ONE key pattern or trend.

{context}

Provide ONE short insight (max 15 words) about their progression.
Examples:
- "You're building intensity steadily - great pacing!"
- "Breathing stabilized after initial spike - you found your rhythm."
- "Intensity dropping - time to push harder?"

Your insight:"""

            message = self.claude_brain.client.messages.create(
                model=self.claude_brain.model,
                max_tokens=50,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": pattern_prompt}
                ]
            )

            insight = message.content[0].text.strip()
            return insight

        except Exception as e:
            print(f"⚠️ Pattern detection error: {e}")
            return None

    def _build_pattern_context(
        self,
        breath_history: list,
        coaching_history: list,
        phase: str
    ) -> str:
        """Build context string for pattern detection."""

        context_parts = [f"Phase: {phase}"]

        # Recent breath trend
        if len(breath_history) >= 3:
            recent = breath_history[-5:]  # Last 5 samples
            intensities = [b.get("intensitet", "?") for b in recent]
            tempos = [b.get("tempo", 0) for b in recent]

            context_parts.append(f"Intensity trend: {' → '.join(intensities)}")
            context_parts.append(f"Tempo range: {min(tempos)}-{max(tempos)} breaths/min")

        # Coaching pattern
        if coaching_history:
            last_messages = [c.get("text", "") for c in coaching_history[-3:]]
            context_parts.append(f"Recent coaching: {', '.join(last_messages)}")

        return "\n".join(context_parts)

    def should_use_pattern_insight(
        self,
        elapsed_seconds: int,
        last_pattern_time: Optional[int]
    ) -> bool:
        """
        STEP 4: Decide if it's time to inject a pattern-based insight.

        Pattern insights are sparse (every 60-90 seconds) to avoid over-coaching.

        Args:
            elapsed_seconds: Total workout time
            last_pattern_time: When last pattern insight was given

        Returns:
            True if pattern insight should be used
        """
        # Don't give pattern insights too early
        if elapsed_seconds < 30:
            return False

        # Don't give pattern insights too frequently
        if last_pattern_time is not None:
            time_since_last = elapsed_seconds - last_pattern_time
            if time_since_last < 60:  # Minimum 60 seconds between pattern insights
                return False

        # Random chance to keep it natural (not every 60 seconds on the dot)
        return random.random() < 0.3  # 30% chance when eligible
