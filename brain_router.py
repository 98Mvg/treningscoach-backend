#
# brain_router.py
# Routes coaching requests to the configured AI brain
#

import os
import random
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
        self.brain_cooldowns = {}
        self.last_route_meta = {
            "provider": "uninitialized",
            "source": "none",
            "status": "uninitialized",
            "mode": None,
            "timestamp": None,
        }
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_brain()

        # STEP 4: Initialize Claude brain for hybrid mode if enabled
        if self.use_hybrid and self.brain_type in ("config", "priority"):
            self._initialize_hybrid_claude()

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
        cooldown_until = self.brain_cooldowns.get(brain_name)
        if cooldown_until and time.time() < cooldown_until:
            remaining = cooldown_until - time.time()
            # Distinguish init failure from runtime cooldown
            if brain_name in self.brain_pool and self.brain_pool[brain_name] is None:
                return f"init_failed (retry in {remaining:.0f}s)"
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

    def _record_failure(self, brain_name: str):
        stats = self.brain_stats.setdefault(brain_name, {"calls": 0, "avg_latency": 0.0, "timeouts": 0, "failures": 0})
        stats["failures"] += 1
        self._set_cooldown(brain_name)

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
            self._record_timeout(brain_name)
            self.brain_last_outcome[brain_name] = {
                "status": "timeout",
                "latency": latency,
                "timeout": timeout,
            }
            print(f"[BRAIN] {brain_name} | TIMEOUT after {latency:.3f}s")
            return None
        except Exception as e:
            latency = time.time() - start
            self._record_failure(brain_name)
            self.brain_last_outcome[brain_name] = {
                "status": "failure",
                "latency": latency,
                "timeout": timeout,
                "error": f"{type(e).__name__}: {e}",
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
        if user_name:
            local_breath_data["user_name"] = user_name
        if self.use_priority_routing and self.priority_brains:
            return self._get_priority_response(local_breath_data, phase, mode, language, persona)
        # STEP 3: Route to appropriate brain mode
        if mode == "realtime_coach":
            # Use optimized real-time coach brain (fast, actionable, no explanations)
            if self.brain is not None:
                try:
                    result = self.brain.get_realtime_coaching(local_breath_data, phase)
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
