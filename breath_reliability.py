"""
Shared breath reliability helpers.

Single source of truth for:
- quality sample derivation
- reliability thresholds
- quality state classification
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _median(values: Iterable[float]) -> Optional[float]:
    cleaned = [float(v) for v in values if v is not None]
    if not cleaned:
        return None
    cleaned.sort()
    n = len(cleaned)
    mid = n // 2
    if n % 2 == 1:
        return cleaned[mid]
    return (cleaned[mid - 1] + cleaned[mid]) / 2.0


def derive_breath_quality_samples(
    *,
    breath_data: Optional[Dict[str, Any]],
    recent_samples: Optional[Iterable[Any]],
    include_current_signal: bool = True,
    max_samples: Optional[int] = None,
) -> List[float]:
    samples: List[float] = []

    if isinstance(recent_samples, (list, tuple)):
        for value in recent_samples:
            parsed = _coerce_float(value)
            if parsed is None:
                continue
            samples.append(max(0.0, min(1.0, parsed)))

    if include_current_signal:
        current_quality = _coerce_float((breath_data or {}).get("signal_quality"))
        if current_quality is not None:
            samples.append(max(0.0, min(1.0, current_quality)))

    if max_samples is not None and max_samples > 0 and len(samples) > max_samples:
        samples = samples[-max_samples:]

    return samples


def is_breath_quality_reliable(
    *,
    sample_count: int,
    median_quality: Optional[float],
    config_module,
) -> bool:
    required_samples = int(getattr(config_module, "CS_BREATH_MIN_RELIABLE_SAMPLES", 6))
    required_quality = float(getattr(config_module, "CS_BREATH_MIN_RELIABLE_QUALITY", 0.35))
    return (
        int(sample_count) >= required_samples
        and median_quality is not None
        and float(median_quality) >= required_quality
    )


def summarize_breath_quality(
    *,
    breath_data: Optional[Dict[str, Any]],
    recent_samples: Optional[Iterable[Any]],
    config_module,
    include_current_signal: bool = True,
    max_samples: Optional[int] = None,
) -> Dict[str, Any]:
    required_samples = int(getattr(config_module, "CS_BREATH_MIN_RELIABLE_SAMPLES", 6))
    required_quality = float(getattr(config_module, "CS_BREATH_MIN_RELIABLE_QUALITY", 0.35))
    degraded_floor = max(0.05, min(0.30, required_quality - 0.15))

    samples = derive_breath_quality_samples(
        breath_data=breath_data,
        recent_samples=recent_samples,
        include_current_signal=include_current_signal,
        max_samples=max_samples,
    )
    sample_count = len(samples)
    median_quality = _median(samples)
    reliable = is_breath_quality_reliable(
        sample_count=sample_count,
        median_quality=median_quality,
        config_module=config_module,
    )

    current_quality = _coerce_float((breath_data or {}).get("signal_quality"))
    if reliable:
        quality_state = "reliable"
    elif (median_quality is not None and median_quality >= degraded_floor) or (
        current_quality is not None and current_quality >= degraded_floor
    ):
        quality_state = "degraded"
    else:
        quality_state = "unavailable"

    return {
        "samples": samples,
        "sample_count": sample_count,
        "median_quality": median_quality,
        "reliable": bool(reliable),
        "quality_state": quality_state,
        "required_samples": required_samples,
        "required_quality": required_quality,
        "degraded_floor": degraded_floor,
    }

