#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import os
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE_PATH = REPO_ROOT / "CODEBASE_GUIDE.md"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BACKEND_SOURCE_OF_TRUTH = [
    "main.py",
    "auth.py",
    "auth_routes.py",
    "brain_router.py",
    "chat_routes.py",
    "web_routes.py",
    "zone_event_motor.py",
    "session_manager.py",
    "database.py",
]

IOS_CORE_FILES = [
    "TreningsCoach/TreningsCoach/TreningsCoachApp.swift",
    "TreningsCoach/TreningsCoach/Views/RootView.swift",
    "TreningsCoach/TreningsCoach/Views/ContentView.swift",
    "TreningsCoach/TreningsCoach/ViewModels/AppViewModel.swift",
    "TreningsCoach/TreningsCoach/ViewModels/HomeViewModel.swift",
    "TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift",
    "TreningsCoach/TreningsCoach/Services/BackendAPIService.swift",
    "TreningsCoach/TreningsCoach/Services/AuthManager.swift",
    "TreningsCoach/TreningsCoach/Services/ContinuousRecordingManager.swift",
    "TreningsCoach/TreningsCoach/Services/WakeWordManager.swift",
    "TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift",
]

WATCH_CORE_FILES = [
    "TreningsCoach/TreningsCoachWatchApp/TreningsCoachWatchApp.swift",
    "TreningsCoach/TreningsCoachWatchApp/WCKeys.swift",
    "TreningsCoach/TreningsCoachWatchApp/WatchRootView.swift",
    "TreningsCoach/TreningsCoachWatchApp/WatchStartWorkoutView.swift",
    "TreningsCoach/TreningsCoachWatchApp/WatchWCManager.swift",
    "TreningsCoach/TreningsCoachWatchApp/WatchWorkoutManager.swift",
]

FEATURES = [
    (
        "Continuous Coaching",
        "Deterministic workout coaching events selected by the backend zone event motor.",
        [
            "main.py",
            "zone_event_motor.py",
            "TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift",
        ],
        "iOS workout runtime -> /coach/continuous",
        "AVFoundation, Flask, zone_event_motor, ElevenLabs/local audio",
        "Workout tab -> Active workout",
    ),
    (
        "Talk To Coach",
        "Short workout-aware Q&A with strict policy guards and talk context injection.",
        [
            "main.py",
            "brain_router.py",
            "session_manager.py",
            "TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift",
        ],
        "Active workout talk button or wake word -> /coach/talk",
        "Speech, brain_router, session_manager, TTS",
        "Active workout",
    ),
    (
        "Workout History",
        "Persists completed workouts to backend and retrieves history for the home screen.",
        [
            "main.py",
            "database.py",
            "TreningsCoach/TreningsCoach/Services/BackendAPIService.swift",
            "TreningsCoach/TreningsCoach/ViewModels/HomeViewModel.swift",
        ],
        "Workout stop -> /workouts and HomeViewModel -> /workouts",
        "SQLAlchemy, auth, BackendAPIService",
        "Workout completion, Home tab",
    ),
    (
        "Apple Watch Start + HR",
        "Watch-gated workout start and HR streaming back to iPhone over WatchConnectivity.",
        [
            "TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift",
            "TreningsCoach/TreningsCoachWatchApp/WatchWCManager.swift",
            "TreningsCoach/TreningsCoachWatchApp/WatchWorkoutManager.swift",
        ],
        "Workout start -> WatchConnectivity",
        "WatchConnectivity, HealthKit",
        "Workout start, Apple Watch app",
    ),
    (
        "BLE + HK Heart Rate",
        "Live BLE heart-rate and HK fallback arbitration for workout coaching.",
        [
            "TreningsCoach/TreningsCoach/Services/HeartRate/BLEHeartRateProvider.swift",
            "TreningsCoach/TreningsCoach/Services/HeartRate/HealthKitFallbackProvider.swift",
            "TreningsCoach/TreningsCoach/Services/HeartRate/HeartRateArbiter.swift",
        ],
        "Workout runtime and monitor discovery",
        "CoreBluetooth, HealthKit",
        "Heart-rate monitors screen, workout runtime",
    ),
    (
        "Auth + Profile",
        "Apple sign-in, token lifecycle, refresh rotation, logout, and profile sync.",
        [
            "auth.py",
            "auth_routes.py",
            "TreningsCoach/TreningsCoach/Services/AuthManager.swift",
            "TreningsCoach/TreningsCoach/ViewModels/AppViewModel.swift",
        ],
        "Onboarding auth, app launch, profile screens",
        "JWT, refresh tokens, Keychain, /auth/*, /profile/upsert",
        "Onboarding, Profile",
    ),
    (
        "Landing + Waitlist",
        "Public marketing pages, waitlist capture, analytics beacon, and preview variants.",
        [
            "web_routes.py",
            "templates/index_launch.html",
            "templates/index_codex.html",
            "templates/site_compare.html",
        ],
        "Web request -> Flask web routes",
        "Flask templates, database waitlist model",
        "Web only",
    ),
]

DORMANT_ITEMS = [
    ("Dead Code", "coaching_pipeline.py", "run / CoachingDecision", "No active runtime callers found; continuous coaching now flows directly through main.py and zone_event_motor.py.", "high"),
    ("Dead Code", "coaching_intelligence.py", "check_safety_override and related helpers", "Static inspection found only calculate_next_interval actively referenced from the main runtime.", "high"),
    ("Legacy System", "main.py", "POST /analyze", "Present in backend, but no active iOS caller was found; current app runtime uses /coach/continuous instead.", "high"),
    ("Partially Implemented Feature", "TreningsCoach/TreningsCoach/Services/AuthManager.swift", "Google/Facebook/Vipps sign-in", "Explicit TODOs and placeholder tokens remain.", "high"),
    ("Partially Implemented Feature", "TreningsCoach/TreningsCoach/Views/Onboarding/AuthView.swift", "Email/password register flow", "UI exists, but no real backend email/password auth path exists in the current runtime.", "high"),
    ("Possible Future Feature", "chat_routes.py", "/chat/*", "Documented and tested, but not wired from the current iOS/watch product UI.", "medium"),
    ("Dead Code", "TreningsCoach/TreningsCoach/ViewModels/HomeViewModel.swift", "recentWorkouts / stats consumption", "HomeView fetches history and computes stats that are not actually rendered by HomeView.", "high"),
    ("Dead Code", "TreningsCoach/TreningsCoach/Views/Components", "GlassCardView / WeeklyProgressRing / StatCardView / WaveformView / CoachOrbView / RecentWorkoutRow", "Static search found definitions but no active references from navigation or runtime views.", "high"),
]

RISKS = [
    ("Critical", "WorkoutViewModel god object", "TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift", "3381-line runtime owner handles workout state, audio, talk, HR, watch, scoring, and persistence. Small edits have wide blast radius."),
    ("Critical", "Backend god object", "main.py", "4296-line Flask assembly file mixes web, auth-adjacent runtime behavior, workout routes, TTS, validation, and persistence concerns."),
    ("High", "In-memory session context under Gunicorn", "session_manager.py", "Talk history and recent event memory are process-local and will not naturally survive multi-worker or restart scenarios."),
    ("High", "Mixed persistence layers", "database.py, user_memory.py, AppViewModel.swift, AuthManager.swift", "DB, JSON, UserDefaults, Keychain, and in-memory state coexist without a single persistence contract."),
    ("High", "Placeholder auth surface remains in app code", "TreningsCoach/TreningsCoach/Services/AuthManager.swift", "Some providers are feature-gated but still implemented with placeholder tokens, increasing future regression and product-truth risk."),
    ("Medium", "Oversized UI containers", "TreningsCoach/TreningsCoach/Views/Onboarding/OnboardingContainerView.swift, TreningsCoach/TreningsCoach/Views/Tabs/WorkoutLaunchView.swift", "Large view files mix layout, interaction, and workflow state, which makes UI changes slower and more error-prone."),
    ("Medium", "Source-of-truth ambiguity from wrappers and legacy docs", "backend/*, docs/*", "The active runtime is in root files, but wrapper files and historical docs increase the chance of editing the wrong place."),
]

RECENT_SESSION_LEARNINGS = [
    (
        "2026-03-10 — Watch Surface, Live Voice Scope, And Wake-Word Handoff",
        "docs/plans/2026-03-10-session-learnings-watch-surface-live-voice-and-wakeword-hardening.md",
        [
            "The watch app now has watch-specific icon assets and a real running dashboard with BPM primary and remaining/elapsed time secondary.",
            "Post-workout `Talk to Coach Live` is visually aligned with the in-workout coach CTA without changing the backend/runtime path.",
            "Wake-word workout-talk handoff now suspends recognition more gracefully, and live voice remains summary-only instead of using full history.",
        ],
    ),
    (
        "2026-03-05 — Talk Safety + Security Hardening",
        "docs/plans/2026-03-05-session-learnings-talk-safety-and-security-hardening.md",
        [
            "Strict `/coach/talk` safety gate added on the single existing runtime path.",
            "Mobile auth/token lifecycle was hardened with refresh rotation and logout support.",
            "Security changes require tests in the same changeset and no parallel auth/runtime path.",
        ],
    ),
    (
        "2026-03-05 — Watch Capability Hardening + Short-Line Audit",
        "docs/plans/2026-03-05-session-learnings-watch-capability-hardening-and-short-lines-audit.md",
        [
            "iPhone watch start/stop now depends on a single `WatchCapabilityState` model.",
            "No-watch states must not call WC transport APIs.",
            "Short-line enforcement was audited but not fully migrated in that pass.",
        ],
    ),
    (
        "2026-03-07 — V2 Voice Unification And Full Bundle",
        "docs/plans/2026-03-07-session-learnings-v2-voice-unification-and-bundle.md",
        [
            "V2 audio generation now forces one EN voice and one NO voice for the approved active set.",
            "The iOS bundle is rebuilt from the V2 manifest instead of the old curated subset.",
            "Infrastructure IDs like `wake_ack.*` and `welcome.standard.1-5` remain required bundle content.",
        ],
    ),
]

CURRENT_STATUS = [
    "Deterministic workout ownership still belongs to `zone_event_motor.py` and must remain there.",
    "Root Flask runtime at the repository root remains the active backend source of truth; `backend/` stays as compatibility wrappers only.",
    "V2 phrase review, promotion, pack generation, R2 sync, and full bundle rebuild exist as the active audio workflow.",
    "Apple Sign-In is enabled in the iPhone app target, and Apple auth is the only real launch-safe mobile provider path in the current app build.",
    "Watch capability gating, companion embedding/signing, request-id correlation, and local fallback semantics are implemented on the existing WatchConnectivity path.",
    "The watch app now ships watch-specific app-icon assets and a running dashboard with large BPM plus local remaining/elapsed time.",
    "Live HR from the watch can reach the iPhone over the current WC path on real paired devices when the companion app is installed.",
    "Workout talk is Grok-first for wake-word and button triggers, but still depends on backend latency and the current talk capture path.",
    "Wake-word workout talk now suspends speech recognition more gracefully before capture to reduce `kAFAssistantErrorDomain Code=1101` churn on device.",
    "Post-workout xAI live voice with Rex is enabled by default, tier-limited, and isolated from the continuous workout runtime.",
    "`Talk to Coach Live` uses sanitized post-workout summary context only, not full user/workout history, and falls back to the existing `/coach/talk` path.",
    "Launch-ready Coachi settings, FAQ, support, privacy-policy, and terms surfaces are now live in SwiftUI and aligned with the docs under `docs/settings` and `docs/legal`.",
]

PHASE_STATUS = [
    (
        "Phase 1",
        "Voice + NO/EN experience",
        "Mostly done / launchable",
        "V2 NO/EN voice workflow, launch-safe settings/legal/support, Apple Sign-In enablement, watch icon/dashboard polish, and summary live-voice CTA parity are implemented.",
        "Finish deployed phrase-rotation, coach-score, and no-HR audits on real devices / live backend.",
    ),
    (
        "Phase 2",
        "Deterministic event motor",
        "Done with guarded follow-ups",
        "Deterministic ownership remains in `zone_event_motor.py`; talk safety, auth hardening, rate limiting, and live-voice isolation are on the single runtime path.",
        "Complete targeted dead-code cleanup and final production launch smoke without touching the continuous runtime architecture.",
    ),
    (
        "Phase 3",
        "Sensor layer (Watch HR/cadence + fallback)",
        "Partial but launch-usable",
        "Watch capability gating, companion embedding/signing, request correlation, HR backfeed, local fallback behavior, and the watch running dashboard are implemented.",
        "Run longer paired-device soak tests for reachability transitions, start ACK edge cases, and any cadence/live-pulse follow-up.",
    ),
    (
        "Phase 4",
        "LLM as language layer only",
        "Controlled / partial rollout",
        "Grok-first workout talk and xAI live voice now sit on constrained language surfaces, while continuous coaching remains deterministic-first.",
        "Validate deployed xAI live voice rollout, free/premium limits, and keep the summary-only memory boundary explicit unless product policy changes.",
    ),
]

KNOWN_REMAINING_STEPS = [
    ("Phase 1", "Deployed phrase and coach-score audit", "Finish real-device and deployed validation for phrase rotation, coach-score credibility, and audio/source parity."),
    ("Phase 1", "No-HR launch validation", "Verify no-HR structure coaching, local-pack vs backend TTS behavior, and score ceilings on real sessions."),
    ("Phase 1", "Launch ops smoke", "Run `scripts/release_check.sh`, live voice smoke, and final landing/mail smoke once Render and production envs are confirmed live."),
    ("Phase 2", "Targeted dead-code cleanup", "Delete only verified dormant paths that reduce launch risk without introducing a second runtime architecture."),
    ("Phase 2", "Premium follow-up architecture", "Keep free-mode/tiered live voice as-is until StoreKit, durable entitlements, paywalls, and restore-purchase flows are genuinely real."),
    ("Phase 3", "Watch soak testing", "Continue paired-device testing for `watchReady` <-> `watchInstalledNotReachable` transitions, delayed ACK behavior, and longer workout sessions."),
    ("Phase 3", "Wake-word device validation", "Repeat wake-word talk capture on physical devices and confirm the local speech-service churn stays suppressed after the suspend handoff change."),
    ("Phase 4", "xAI live rollout validation", "Validate deployed xAI live voice sessions, free/premium limits, fallback behavior, and session-duration policy with real accounts."),
    ("Phase 4", "Explicit memory policy", "If broader history is ever added to live voice, document it as a deliberate product change; current truth is summary-only context."),
]


def _file_link(path: str) -> str:
    return f"[{Path(path).name}]({REPO_ROOT / path})"


def _abs(path: str) -> str:
    return str(REPO_ROOT / path)


def _load_routes() -> list[tuple[str, str, str]]:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        import importlib

        main = importlib.import_module("main")

    routes = []
    for rule in sorted(main.app.url_map.iter_rules(), key=lambda item: item.rule):
        if rule.endpoint == "static":
            continue
        methods = ", ".join(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"}))
        routes.append((rule.rule, methods, rule.endpoint))
    return routes


def _route_group(route: str) -> str:
    if route.startswith("/auth/"):
        return "Auth"
    if route.startswith("/coach/") or route in {"/welcome", "/workouts", "/profile/upsert", "/analyze"} or route.startswith("/download/"):
        return "Workout Runtime"
    if route.startswith("/brain/") or route.startswith("/chat/"):
        return "Chat And Ops"
    return "Web And Landing"


def _format_routes() -> str:
    groups: dict[str, list[tuple[str, str, str]]] = {
        "Workout Runtime": [],
        "Auth": [],
        "Chat And Ops": [],
        "Web And Landing": [],
    }
    for route, methods, endpoint in _load_routes():
        groups[_route_group(route)].append((route, methods, endpoint))

    lines: list[str] = []
    for group_name, items in groups.items():
        lines.append(f"### {group_name}")
        lines.append("")
        lines.append("| Route | Methods | Endpoint |")
        lines.append("|---|---|---|")
        for route, methods, endpoint in items:
            lines.append(f"| `{route}` | `{methods}` | `{endpoint}` |")
        lines.append("")
    return "\n".join(lines).rstrip()


def _project_tree() -> str:
    return dedent(
        f"""
        ```text
        {REPO_ROOT}
        ├── main.py
        ├── auth.py
        ├── auth_routes.py
        ├── brain_router.py
        ├── chat_routes.py
        ├── web_routes.py
        ├── zone_event_motor.py
        ├── session_manager.py
        ├── database.py
        ├── brains/
        ├── templates/
        ├── tests_phaseb/
        ├── alembic/
        ├── scripts/
        ├── TreningsCoach/
        │   ├── TreningsCoach/
        │   │   ├── Models/
        │   │   ├── Services/
        │   │   │   ├── HeartRate/
        │   │   │   └── WC/
        │   │   ├── ViewModels/
        │   │   ├── Views/
        │   │   └── TreningsCoachApp.swift
        │   └── TreningsCoachWatchApp/
        │       ├── TreningsCoachWatchApp.swift
        │       ├── WatchWCManager.swift
        │       ├── WatchWorkoutManager.swift
        │       └── Watch views
        ├── backend/                # compatibility wrappers around root runtime
        └── docs/
        ```
        """
    ).strip()


def _format_file_list(paths: list[str]) -> str:
    return "\n".join(f"- {_file_link(path)}" for path in paths)


def _format_features() -> str:
    lines: list[str] = []
    for name, description, files, entry, deps, ui in FEATURES:
        lines.append(f"### Feature: {name}")
        lines.append(f"Description: {description}")
        lines.append("Primary files:")
        lines.extend(f"- {_file_link(path)}" for path in files)
        lines.append(f"Runtime entry point: {entry}")
        lines.append(f"Dependencies: {deps}")
        lines.append(f"Frontend UI entry: {ui}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_dormant_items() -> str:
    lines = ["| Category | File | Function/Class/System | Why It Appears Unused | Confidence |", "|---|---|---|---|---|"]
    for category, file, item, why, confidence in DORMANT_ITEMS:
        lines.append(f"| {category} | [{Path(file).name}]({_abs(file)}) | `{item}` | {why} | {confidence} |")
    return "\n".join(lines)


def _format_risks() -> str:
    lines = ["| Severity | Risk | File(s) | Impact |", "|---|---|---|---|"]
    for severity, risk, files, impact in RISKS:
        refs = ", ".join(f"[{Path(p.strip()).name}]({_abs(p.strip())})" for p in files.split(","))
        lines.append(f"| {severity} | {risk} | {refs} | {impact} |")
    return "\n".join(lines)


def _format_recent_session_learnings() -> str:
    lines: list[str] = []
    for title, path, bullets in RECENT_SESSION_LEARNINGS:
        lines.append(f"### [{title}]({_abs(path)})")
        for bullet in bullets:
            lines.append(f"- {bullet}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_current_status() -> str:
    return "\n".join(f"- {item}" for item in CURRENT_STATUS)


def _format_phase_status() -> str:
    lines = ["| Phase | Scope | Status | Done | Missing |", "|---|---|---|---|---|"]
    for phase, scope, status, done, missing in PHASE_STATUS:
        lines.append(f"| {phase} | {scope} | {status} | {done} | {missing} |")
    return "\n".join(lines)


def _format_remaining_steps() -> str:
    lines = ["| Phase | Track | Remaining Work |", "|---|---|---|"]
    for phase, track, work in KNOWN_REMAINING_STEPS:
        lines.append(f"| {phase} | {track} | {work} |")
    return "\n".join(lines)


def build_guide() -> str:
    guide = dedent(
        f"""
        # CODEBASE GUIDE

        > Generated file. Do not edit by hand.
        > Source: [scripts/generate_codebase_guide.py]({REPO_ROOT / 'scripts/generate_codebase_guide.py'})
        > Regenerate with: `python3 scripts/generate_codebase_guide.py`
        > Verify sync with: `pytest -q tests_phaseb/test_codebase_guide_sync.py`

        Last generated: {date.today().isoformat()}
        Repository: `{REPO_ROOT}`

        ## Agent Quickstart

        1. The deterministic workout runtime is the product core.
           - Continuous workout coaching must remain owned by [{Path('zone_event_motor.py').name}]({_abs('zone_event_motor.py')}).
           - AI may rewrite phrasing or answer questions, but must not decide workout events.

        2. The active backend source of truth is at the repository root.
           - Edit root runtime files first.
           - Treat `backend/` as compatibility wrappers unless you verify otherwise.

        3. The active iOS runtime is centered on one large orchestrator.
           - [{Path('TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift').name}]({_abs('TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift')}) owns most workout behavior.
           - Changes there require focused regression testing.

        4. The main runtime paths are:
           - Workout tick: iOS -> `/coach/continuous` -> `zone_event_motor`
           - User question: iOS -> `/coach/talk` -> `brain_router`
           - Workout history: iOS -> `/workouts`
           - Watch HR: iPhone `PhoneWCManager` <-> watch `WatchWCManager`

        ## 1. Product Overview

        TreningsCoach is a running-coach product with a SwiftUI iPhone app, a watchOS companion app, and a Flask backend. The primary experience is live workout coaching during runs. The iPhone app manages workout setup, session state, audio capture, wake-word input, heart-rate sources, and playback. The backend receives workout context and audio, uses a deterministic event engine to decide what coaching event should happen, optionally rewrites the wording, generates or resolves audio, and returns a short coaching response. The same backend also supports talk-to-coach Q&A, auth/profile/history APIs, and a separate landing/waitlist web surface.

        Primary users:
        - iPhone runners doing guided workouts
        - Apple Watch users who want live HR and watch-confirmed workout start
        - BLE HR sensor users
        - Web visitors joining the waitlist or previewing the product

        Core user flows:
        - onboarding -> optional auth -> workout setup -> workout start -> continuous coaching
        - active workout -> wake word or talk button -> `/coach/talk`
        - workout completion -> save history -> show score/completion UI
        - profile/settings -> update language, personal data, heart-rate monitor info
        - watch path -> request start on watch -> confirm on watch -> HR streams back to phone

        Non-goals / do-not-break boundary:
        - Continuous coaching decisions must stay deterministic-first under [{Path('zone_event_motor.py').name}]({_abs('zone_event_motor.py')}).
        - AI must not become the owner of workout event timing or selection.

        ## 2. Stack And Top-Level Layout

        ### Stack

        | Layer | Stack |
        |---|---|
        | iOS | SwiftUI, AVFoundation, Speech, HealthKit, CoreBluetooth, WatchConnectivity |
        | watchOS | SwiftUI, HealthKit, WatchConnectivity |
        | Backend | Python 3, Flask, SQLAlchemy, Gunicorn |
        | AI/TTS | Multi-brain router + ElevenLabs TTS |
        | Data | SQLite/PostgreSQL, Keychain, UserDefaults, JSON files, in-memory session store |
        | Web | Flask templates and lightweight frontend JS |

        ### High-level tree

        {_project_tree()}

        ## 3. Runtime Entry Points

        ### Backend
        - Production entry: [{Path('Procfile').name}]({_abs('Procfile')}) -> `gunicorn main:app`
        - Flask app assembly: [{Path('main.py').name}]({_abs('main.py')})

        ### iOS
        - App entry: [{Path('TreningsCoach/TreningsCoach/TreningsCoachApp.swift').name}]({_abs('TreningsCoach/TreningsCoach/TreningsCoachApp.swift')})
        - Root gate: [{Path('TreningsCoach/TreningsCoach/Views/RootView.swift').name}]({_abs('TreningsCoach/TreningsCoach/Views/RootView.swift')})
        - Main shell: [{Path('TreningsCoach/TreningsCoach/Views/ContentView.swift').name}]({_abs('TreningsCoach/TreningsCoach/Views/ContentView.swift')})

        ### watchOS
        - App entry: [{Path('TreningsCoach/TreningsCoachWatchApp/TreningsCoachWatchApp.swift').name}]({_abs('TreningsCoach/TreningsCoachWatchApp/TreningsCoachWatchApp.swift')})
        - Root view: [{Path('TreningsCoach/TreningsCoachWatchApp/WatchRootView.swift').name}]({_abs('TreningsCoach/TreningsCoachWatchApp/WatchRootView.swift')})

        ## 4. Architecture Map

        ```mermaid
        flowchart LR
            IOS["iOS App\\nSwiftUI"]
            WATCH["watchOS App\\nSwiftUI + HKWorkoutSession"]
            BACKEND["Flask Backend\\nmain.py"]
            ZONE["zone_event_motor.py\\nDeterministic event owner"]
            BRAIN["brain_router.py\\nTalk + rewrite only"]
            SESSION["session_manager.py\\nTalk history + recent events"]
            DB["SQLAlchemy DB\\nusers/profile/workouts/tokens/waitlist"]
            TTS["ElevenLabs TTS\\n+ audio file serving"]
            WEB["web_routes.py + templates\\nlanding / waitlist / analytics"]

            IOS -->|"/coach/continuous\\n/coach/talk\\n/workouts\\n/welcome\\n/auth"| BACKEND
            IOS <-->|"WatchConnectivity"| WATCH
            IOS -->|"BLE / HealthKit"| IOS
            BACKEND --> ZONE
            BACKEND --> BRAIN
            BACKEND --> SESSION
            BACKEND --> DB
            BACKEND --> TTS
            BACKEND --> WEB
        ```

        ### Backend service ownership

        {_format_file_list(BACKEND_SOURCE_OF_TRUTH)}

        ### iOS core runtime files

        {_format_file_list(IOS_CORE_FILES)}

        ### watchOS core runtime files

        {_format_file_list(WATCH_CORE_FILES)}

        ## 5. Backend Route Inventory

        {_format_routes()}

        ## 6. Watch Communication Flow

        ```mermaid
        flowchart LR
            A["WorkoutViewModel"] --> B["PhoneWCManager"]
            B -->|"sendMessage / updateApplicationContext"| C["WatchWCManager"]
            C --> D["WatchStartWorkoutView"]
            D --> E["WatchWorkoutManager"]
            E -->|"HKWorkoutSession + Builder"| F["Apple Watch sensors"]
            E -->|"workout_started / failed / stopped + HR"| B
            B --> G["AppleWatchWCProvider"]
            G --> H["HeartRateArbiter"]
            H --> A
        ```

        Key watch capability states on iPhone live in [{Path('TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift').name}]({_abs('TreningsCoach/TreningsCoach/Services/PhoneWCManager.swift')}):
        - `noWatchSupport`
        - `watchNotInstalled`
        - `watchInstalledNotReachable`
        - `watchReady`

        ## 7. Voice Pipeline

        End-to-end voice flow:
        1. iOS starts [{Path('TreningsCoach/TreningsCoach/Services/ContinuousRecordingManager.swift').name}]({_abs('TreningsCoach/TreningsCoach/Services/ContinuousRecordingManager.swift')}).
        2. The same audio stream feeds [{Path('TreningsCoach/TreningsCoach/Services/WakeWordManager.swift').name}]({_abs('TreningsCoach/TreningsCoach/Services/WakeWordManager.swift')}).
        3. Workout ticks export audio chunks and call `/coach/continuous`.
        4. Talk button or wake-word flow captures a short utterance and calls `/coach/talk`.
        5. Backend produces text and `audio_url` metadata.
        6. iOS prefers bundled or synced audio-pack files, then falls back to downloading backend audio.
        7. iOS plays the resolved audio.

        Main voice files:
        - [{Path('TreningsCoach/TreningsCoach/Services/ContinuousRecordingManager.swift').name}]({_abs('TreningsCoach/TreningsCoach/Services/ContinuousRecordingManager.swift')})
        - [{Path('TreningsCoach/TreningsCoach/Services/WakeWordManager.swift').name}]({_abs('TreningsCoach/TreningsCoach/Services/WakeWordManager.swift')})
        - [{Path('TreningsCoach/TreningsCoach/Services/AudioPackSyncManager.swift').name}]({_abs('TreningsCoach/TreningsCoach/Services/AudioPackSyncManager.swift')})
        - [{Path('TreningsCoach/TreningsCoach/Services/AudioPipelineDiagnostics.swift').name}]({_abs('TreningsCoach/TreningsCoach/Services/AudioPipelineDiagnostics.swift')})
        - [{Path('main.py').name}]({_abs('main.py')})
        - [{Path('elevenlabs_tts.py').name}]({_abs('elevenlabs_tts.py')})
        - [{Path('tts_phrase_catalog.py').name}]({_abs('tts_phrase_catalog.py')})

        ## 8. Workout Runtime Pipeline

        ```mermaid
        flowchart LR
            UI["WorkoutLaunchView / ActiveWorkoutView"] --> VM["WorkoutViewModel"]
            VM --> HR["HeartRateArbiter"]
            VM --> REC["ContinuousRecordingManager"]
            VM --> API["BackendAPIService"]
            API --> CONT["POST /coach/continuous"]
            CONT --> ZONE["zone_event_motor"]
            ZONE --> REWRITE["optional phrasing rewrite"]
            REWRITE --> TTS["audio resolution / TTS"]
            TTS --> RESP["response payload"]
            RESP --> VM
            VM --> PLAY["audio playback + UI updates"]
        ```

        Ownership rules:
        - Event timing, selection, and deterministic progression belong to [{Path('zone_event_motor.py').name}]({_abs('zone_event_motor.py')}).
        - The backend may validate or rewrite event phrasing, but must not change the event meaning or event timing contract.
        - Talk-to-coach belongs to [{Path('brain_router.py').name}]({_abs('brain_router.py')}), not `zone_event_motor`.

        ## 9. Feature Inventory

        {_format_features()}

        ## 10. Dead Code And Dormant Systems

        {_format_dormant_items()}

        ## 11. Architectural Risks

        {_format_risks()}

        ## 12. Persistence And Integrations

        Backend DB tables defined in [{Path('database.py').name}]({_abs('database.py')}):
        - `users`
        - `user_settings`
        - `user_profiles`
        - `workout_history`
        - `refresh_tokens`
        - `waitlist_signups`

        Other stores:
        - Keychain for tokens and expiries
        - UserDefaults for onboarding state, profile fields, and app settings
        - JSON files for some memory/personalization stores
        - in-memory [{Path('session_manager.py').name}]({_abs('session_manager.py')}) sessions and talk context

        Main integrations:
        - xAI Grok
        - Google Gemini
        - OpenAI
        - Anthropic Claude
        - ElevenLabs TTS
        - Apple Sign-In
        - Apple Watch / WatchConnectivity
        - BLE HR devices
        - HealthKit

        ## 13. Recent Session Learnings

        {_format_recent_session_learnings()}

        ## 14. Current Operational Status

        {_format_current_status()}

        ## 15. Phase 1-4 Status Snapshot

        {_format_phase_status()}

        ## 16. Remaining Roadmap

        {_format_remaining_steps()}

        ## 17. Documentation Hygiene Rules

        1. This file is generated. Update [{Path('scripts/generate_codebase_guide.py').name}]({_abs('scripts/generate_codebase_guide.py')}) and regenerate.
        2. The sync contract lives in [test_codebase_guide_sync.py]({_abs('tests_phaseb/test_codebase_guide_sync.py')}).
        3. Release checks should fail if this guide drifts from the generator.
        4. Runtime code is more authoritative than historical docs.

        ## 18. Final Rule

        When in doubt:
        - preserve the single existing runtime path
        - keep `zone_event_motor` as the deterministic workout-event owner
        - prefer modifying the current path over introducing a parallel system
        - trust runtime code over historical docs
        """
    ).strip()
    guide = re.sub(r"(?m)^ {8}", "", guide)
    return guide + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CODEBASE_GUIDE.md from the current repo source of truth.")
    parser.add_argument("--stdout", action="store_true", help="Print generated guide to stdout instead of writing the file.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if CODEBASE_GUIDE.md is out of sync.")
    args = parser.parse_args()

    guide = build_guide()

    if args.stdout:
        sys.stdout.write(guide)
        return 0

    if args.check:
        current = GUIDE_PATH.read_text(encoding="utf-8") if GUIDE_PATH.exists() else ""
        if current != guide:
            print("[FAIL] CODEBASE_GUIDE.md is out of sync. Run: python3 scripts/generate_codebase_guide.py")
            return 1
        print("[OK] CODEBASE_GUIDE.md is in sync")
        return 0

    GUIDE_PATH.write_text(guide, encoding="utf-8")
    print(f"[OK] Wrote {GUIDE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
