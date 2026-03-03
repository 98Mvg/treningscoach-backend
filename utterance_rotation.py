from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path


_STATE_LOCK = threading.Lock()
_DEFAULT_STATE_PATH = (
    Path(__file__).resolve().parent
    / "output"
    / "cache"
    / "utterance_rotation_state.json"
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "history": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("state payload is not an object")
        history = payload.get("history")
        if not isinstance(history, dict):
            payload["history"] = {}
        return payload
    except (OSError, json.JSONDecodeError, ValueError):
        return {"version": 1, "history": {}}


def _save_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _rotation_key(category_prefix: str, language: str, persona: str) -> str:
    return f"{category_prefix}|{language}|{persona}"


def _normalized_ids(available_ids: list[str]) -> list[str]:
    return sorted({str(item).strip() for item in available_ids if str(item).strip()})


def select_rotated_utterance(
    *,
    category_prefix: str,
    language: str,
    persona: str,
    available_ids: list[str],
    recent_k: int = 2,
    avoid_hours: int = 24,
    history_limit: int = 50,
    state_path: Path | None = None,
    now_utc: datetime | None = None,
) -> str:
    """
    Select a stable utterance ID with anti-repeat behavior.

    Rules:
    - Prefer IDs not used in last K plays.
    - Prefer IDs not used within avoid_hours.
    - If all are constrained, gracefully fall back.
    """
    ids = _normalized_ids(available_ids)
    if not ids:
        raise ValueError("available_ids cannot be empty")
    if len(ids) == 1:
        return ids[0]

    effective_now = now_utc.astimezone(timezone.utc) if now_utc else _utc_now()
    effective_recent_k = max(0, int(recent_k))
    effective_avoid_hours = max(0, int(avoid_hours))
    effective_history_limit = max(10, int(history_limit))
    store_path = state_path or _DEFAULT_STATE_PATH
    key = _rotation_key(category_prefix, language, persona)

    with _STATE_LOCK:
        state = _load_state(store_path)
        history_map = state.setdefault("history", {})
        raw_history = history_map.get(key, [])
        if not isinstance(raw_history, list):
            raw_history = []

        history: list[dict] = []
        for item in raw_history:
            if not isinstance(item, dict):
                continue
            phrase_id = str(item.get("id", "")).strip()
            if not phrase_id:
                continue
            ts = _parse_iso(str(item.get("ts", "")).strip())
            history.append({"id": phrase_id, "ts": ts.isoformat() if ts else None})

        recent_ids = [entry["id"] for entry in history if entry.get("id")]
        if effective_recent_k > 0:
            recent_ids = recent_ids[-effective_recent_k:]
        else:
            recent_ids = []
        recent_set = set(recent_ids)

        cutoff = effective_now - timedelta(hours=effective_avoid_hours)
        last_used_ts: dict[str, datetime] = {}
        for entry in history:
            phrase_id = entry.get("id")
            parsed_ts = _parse_iso(entry.get("ts"))
            if not phrase_id or parsed_ts is None:
                continue
            existing = last_used_ts.get(phrase_id)
            if existing is None or parsed_ts > existing:
                last_used_ts[phrase_id] = parsed_ts

        recently_used_time = {
            phrase_id
            for phrase_id, ts in last_used_ts.items()
            if ts >= cutoff
        }

        eligible = [
            phrase_id
            for phrase_id in ids
            if phrase_id not in recent_set and phrase_id not in recently_used_time
        ]
        if not eligible:
            eligible = [phrase_id for phrase_id in ids if phrase_id not in recent_set]
        if not eligible:
            eligible = [phrase_id for phrase_id in ids if phrase_id not in recently_used_time]
        if not eligible:
            eligible = ids

        last_id = history[-1]["id"] if history else None
        if last_id in ids:
            start_idx = ids.index(last_id)
            ordered = [ids[(start_idx + step) % len(ids)] for step in range(1, len(ids) + 1)]
        else:
            ordered = ids

        chosen = next((phrase_id for phrase_id in ordered if phrase_id in eligible), eligible[0])

        history.append({"id": chosen, "ts": effective_now.isoformat()})
        history_map[key] = history[-effective_history_limit:]
        state["updated_at"] = effective_now.isoformat()
        _save_state(store_path, state)

    return chosen

