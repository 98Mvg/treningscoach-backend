#
# breath_analyzer.py
# Advanced breath analysis using DSP + spectral features
#
# Replaces the naive amplitude-based analyze_breath() with:
# - Band-pass filtering (100-1000Hz) to isolate breath sounds
# - MFCC + spectral feature extraction
# - Rule-based inhale/exhale/pause classification
# - Real respiratory rate, regularity, and I:E ratio computation
#

import logging
import numpy as np
import scipy.signal
import librosa

logger = logging.getLogger(__name__)

# ============================================
# BREATH ANALYZER
# ============================================

class BreathAnalyzer:
    """
    Real-time breath phase classifier using DSP and spectral features.

    Pipeline:
    1. Load WAV audio (librosa)
    2. Band-pass filter 100-1000Hz (Butterworth)
    3. Noise gate (adaptive RMS threshold)
    4. Feature extraction (RMS, MFCC, spectral centroid, ZCR)
    5. Breath event detection (energy envelope peaks)
    6. Phase classification (inhale/exhale/pause via spectral heuristics)
    7. Summary metrics (respiratory rate, regularity, I:E ratio)
    """

    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate

        # Frame parameters: 25ms windows, 10ms hop
        self.frame_length = int(0.025 * sample_rate)   # 1102 samples
        self.hop_length = int(0.010 * sample_rate)      # 441 samples

        # Pre-compute Butterworth band-pass filter coefficients (100-1000Hz)
        # Isolates breath sounds, removes low-freq rumble and high-freq noise
        self.sos = scipy.signal.butter(
            N=4,
            Wn=[100, 1000],
            btype='bandpass',
            fs=sample_rate,
            output='sos'
        )

        # Classification thresholds (tunable)
        self.centroid_threshold = 400.0       # Hz: inhale > this, exhale < this
        self.min_breath_duration = 0.2        # seconds: ignore events shorter than this
        self.max_breath_duration = 5.0        # seconds: ignore events longer than this
        self.min_pause_duration = 0.3         # seconds: gaps shorter than this aren't pauses
        self.noise_gate_factor = 2.0          # multiply noise floor by this for gate threshold
        self.rms_smoothing_kernel = 15        # median filter kernel (~150ms at 10ms hop)
        self.energy_threshold_factor = 0.5    # fraction of mean RMS for event detection

        logger.info("BreathAnalyzer initialized (sr=%d, frame=%d, hop=%d)",
                     sample_rate, self.frame_length, self.hop_length)

    # ============================================
    # MAIN ENTRY POINT
    # ============================================

    def analyze(self, audio_file_path: str) -> dict:
        """
        Analyze an audio file and return breath metrics.

        Drop-in replacement for the old analyze_breath() function.
        Returns backward-compatible dict with additional new fields.
        """
        try:
            # 1. Load audio
            signal = self._load_audio(audio_file_path)
            if signal is None or len(signal) == 0:
                return self._default_analysis()

            duration = len(signal) / self.sample_rate

            # 2. Pre-process: band-pass filter + noise gate
            filtered = self._bandpass_filter(signal)
            gated, noise_floor = self._noise_gate(filtered)

            # 3. Extract features
            features = self._extract_features(gated)

            # 4. Detect breath events from energy envelope
            events = self._detect_breath_events(features['rms'])

            # 5. Classify each event as inhale or exhale
            breath_phases = self._classify_events(
                events, features['spectral_centroid'], features['rms']
            )

            # 6. Insert pauses between events
            breath_phases = self._insert_pauses(breath_phases, duration)

            # 7. Compute summary metrics
            metrics = self._compute_metrics(breath_phases, features, signal, noise_floor, duration)

            # 8. Build backward-compatible response
            result = {
                # EXISTING fields (backward-compatible)
                "silence": metrics['silence_percent'],
                "volume": metrics['volume'],
                "tempo": metrics['respiratory_rate'],  # Now REAL respiratory rate
                "intensity": metrics['intensity'],
                "duration": round(duration, 2),

                # NEW fields
                "breath_phases": breath_phases,
                "respiratory_rate": metrics['respiratory_rate'],
                "breath_regularity": metrics['breath_regularity'],
                "inhale_exhale_ratio": metrics['inhale_exhale_ratio'],
                "signal_quality": metrics['signal_quality'],
                "dominant_frequency": metrics['dominant_frequency'],
            }

            logger.info(
                "Breath analysis: rate=%.1f bpm, regularity=%.2f, I:E=%.2f, "
                "quality=%.2f, intensity=%s, %d phases detected",
                metrics['respiratory_rate'], metrics['breath_regularity'],
                metrics['inhale_exhale_ratio'], metrics['signal_quality'],
                metrics['intensity'], len(breath_phases)
            )

            return result

        except Exception as e:
            logger.error("Breath analysis failed: %s", e, exc_info=True)
            return self._default_analysis()

    # ============================================
    # AUDIO LOADING
    # ============================================

    def _load_audio(self, filepath: str) -> np.ndarray:
        """Load audio file as float32 array normalized to [-1, 1]."""
        try:
            signal, sr = librosa.load(filepath, sr=self.sample_rate, mono=True)
            return signal
        except Exception as e:
            logger.error("Failed to load audio %s: %s", filepath, e)
            return None

    # ============================================
    # PRE-PROCESSING
    # ============================================

    def _bandpass_filter(self, signal: np.ndarray) -> np.ndarray:
        """Apply 100-1000Hz band-pass filter to isolate breath sounds."""
        return scipy.signal.sosfilt(self.sos, signal)

    def _noise_gate(self, signal: np.ndarray) -> tuple:
        """
        Apply adaptive noise gate.
        Returns (gated_signal, noise_floor_estimate).
        """
        # Compute frame-level RMS
        rms = librosa.feature.rms(
            y=signal,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )[0]

        # Estimate noise floor from quietest 10% of frames
        noise_floor = float(np.percentile(rms, 10))
        gate_threshold = noise_floor * self.noise_gate_factor

        # Create per-frame mask
        mask = rms > gate_threshold

        # Expand mask to sample domain
        gated = signal.copy()
        for i, is_active in enumerate(mask):
            if not is_active:
                start = i * self.hop_length
                end = min(start + self.frame_length, len(gated))
                gated[start:end] = 0.0

        return gated, noise_floor

    # ============================================
    # FEATURE EXTRACTION
    # ============================================

    def _extract_features(self, signal: np.ndarray) -> dict:
        """Extract all spectral and temporal features."""

        # RMS energy envelope
        rms = librosa.feature.rms(
            y=signal,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )[0]

        # 13 MFCCs (for future ML use + spectral shape analysis)
        mfcc = librosa.feature.mfcc(
            y=signal,
            sr=self.sample_rate,
            n_mfcc=13,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )

        # Spectral centroid — key discriminator for inhale vs exhale
        spectral_centroid = librosa.feature.spectral_centroid(
            y=signal,
            sr=self.sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )[0]

        # Zero-crossing rate — helps separate breath from noise
        zcr = librosa.feature.zero_crossing_rate(
            signal,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )[0]

        # Spectral rolloff — confirms breath vs non-breath
        rolloff = librosa.feature.spectral_rolloff(
            y=signal,
            sr=self.sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )[0]

        return {
            'rms': rms,
            'mfcc': mfcc,
            'spectral_centroid': spectral_centroid,
            'zcr': zcr,
            'rolloff': rolloff,
        }

    # ============================================
    # BREATH EVENT DETECTION
    # ============================================

    def _detect_breath_events(self, rms: np.ndarray) -> list:
        """
        Detect breath events from RMS energy envelope.
        Returns list of (start_frame, end_frame) tuples.
        """
        # Smooth RMS with median filter to remove micro-fluctuations
        kernel = min(self.rms_smoothing_kernel, len(rms))
        if kernel % 2 == 0:
            kernel = max(1, kernel - 1)
        smoothed = scipy.signal.medfilt(rms, kernel_size=kernel)

        # Adaptive threshold
        mean_rms = np.mean(smoothed)
        if mean_rms < 1e-6:
            return []  # Essentially silent
        threshold = mean_rms * self.energy_threshold_factor

        # Find contiguous regions above threshold
        above = smoothed > threshold
        events = []
        in_event = False
        start = 0

        for i in range(len(above)):
            if above[i] and not in_event:
                start = i
                in_event = True
            elif not above[i] and in_event:
                events.append((start, i))
                in_event = False
        if in_event:
            events.append((start, len(above)))

        # Filter by duration
        frame_time = self.hop_length / self.sample_rate
        min_frames = int(self.min_breath_duration / frame_time)
        max_frames = int(self.max_breath_duration / frame_time)

        events = [
            (s, e) for s, e in events
            if min_frames <= (e - s) <= max_frames
        ]

        return events

    # ============================================
    # PHASE CLASSIFICATION
    # ============================================

    def _classify_events(self, events: list, spectral_centroid: np.ndarray,
                         rms: np.ndarray) -> list:
        """
        Classify each breath event as inhale or exhale using spectral heuristics.

        Inhale: higher spectral centroid (>400Hz), turbulent, narrowband
        Exhale: lower spectral centroid (<400Hz), broader spectrum, more energy
        """
        frame_time = self.hop_length / self.sample_rate
        phases = []

        for start_frame, end_frame in events:
            # Safely slice features for this event
            sc_slice = spectral_centroid[start_frame:end_frame]
            rms_slice = rms[start_frame:end_frame]

            if len(sc_slice) == 0 or len(rms_slice) == 0:
                continue

            event_centroid = float(np.mean(sc_slice))
            event_energy = float(np.mean(rms_slice))
            event_duration = (end_frame - start_frame) * frame_time

            # Classification heuristic
            if event_centroid > self.centroid_threshold:
                phase_type = "inhale"
                # Confidence increases with distance from threshold
                confidence = min(0.95, 0.5 + (event_centroid - self.centroid_threshold) / 800)
            else:
                phase_type = "exhale"
                confidence = min(0.95, 0.5 + (self.centroid_threshold - event_centroid) / 400)

            # Duration sanity check: very short events get lower confidence
            if event_duration < 0.3:
                confidence *= 0.7

            phases.append({
                "type": phase_type,
                "start": round(start_frame * frame_time, 3),
                "end": round(end_frame * frame_time, 3),
                "confidence": round(confidence, 2),
                "energy": round(event_energy, 4),
                "spectral_centroid": round(event_centroid, 1),
            })

        return phases

    def _insert_pauses(self, phases: list, total_duration: float) -> list:
        """Insert pause events between breath events where gaps > min_pause_duration."""
        if not phases:
            return phases

        enriched = []

        # Check gap before first event
        if phases[0]['start'] > self.min_pause_duration:
            enriched.append({
                "type": "pause",
                "start": 0.0,
                "end": phases[0]['start'],
                "confidence": 0.8,
            })

        for i, phase in enumerate(phases):
            enriched.append(phase)

            # Check gap to next event
            if i < len(phases) - 1:
                gap = phases[i + 1]['start'] - phase['end']
                if gap > self.min_pause_duration:
                    enriched.append({
                        "type": "pause",
                        "start": phase['end'],
                        "end": phases[i + 1]['start'],
                        "confidence": 0.8,
                    })

        # Check gap after last event
        last_end = phases[-1]['end']
        if (total_duration - last_end) > self.min_pause_duration:
            enriched.append({
                "type": "pause",
                "start": last_end,
                "end": round(total_duration, 3),
                "confidence": 0.8,
            })

        return enriched

    # ============================================
    # SUMMARY METRICS
    # ============================================

    def _compute_metrics(self, breath_phases: list, features: dict,
                         raw_signal: np.ndarray, noise_floor: float,
                         duration: float) -> dict:
        """Compute all summary metrics from detected breath phases."""

        rms = features['rms']

        # --- Volume (backward-compatible, 0-100 scale) ---
        # Use RMS of the raw (pre-gated) signal for volume to avoid noise gate suppression
        raw_rms = librosa.feature.rms(
            y=raw_signal,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )[0]
        mean_rms_raw = float(np.mean(raw_rms))
        # Scale: RMS of [-1,1] signal. Typical breath ~0.005-0.05, speech ~0.03-0.1
        # Amplify and scale to 0-100 (10x amplification for breath-level signals)
        volume = min(100.0, mean_rms_raw * 1000)  # Amplified to 0-100 range

        # --- Silence percent ---
        silent_frames = np.sum(rms < noise_floor * self.noise_gate_factor)
        silence_percent = round(float(silent_frames / max(len(rms), 1)) * 100, 1)

        # --- Respiratory rate (real BPM) ---
        breath_events = [p for p in breath_phases if p['type'] in ('inhale', 'exhale')]

        if len(breath_events) >= 2:
            # Count complete breath cycles
            # A cycle is typically inhale + exhale
            cycle_count = len(breath_events) / 2.0
            respiratory_rate = round((cycle_count / duration) * 60, 1)
            # Clamp to reasonable range
            respiratory_rate = max(4.0, min(60.0, respiratory_rate))
        else:
            respiratory_rate = 15.0  # Default fallback

        # --- Breath regularity (0-1, higher = more regular) ---
        if len(breath_events) >= 3:
            # Compute intervals between consecutive breath event starts
            starts = [e['start'] for e in breath_events]
            intervals = [starts[i+1] - starts[i] for i in range(len(starts)-1)]
            intervals = [iv for iv in intervals if iv > 0]

            if intervals and np.mean(intervals) > 0:
                cv = float(np.std(intervals) / np.mean(intervals))  # Coefficient of variation
                breath_regularity = round(max(0.0, min(1.0, 1.0 - cv)), 2)
            else:
                breath_regularity = 0.5
        else:
            breath_regularity = 0.5  # Neutral default

        # --- Inhale/Exhale ratio ---
        inhales = [p for p in breath_phases if p['type'] == 'inhale']
        exhales = [p for p in breath_phases if p['type'] == 'exhale']

        if inhales and exhales:
            avg_inhale = np.mean([p['end'] - p['start'] for p in inhales])
            avg_exhale = np.mean([p['end'] - p['start'] for p in exhales])
            if avg_exhale > 0:
                inhale_exhale_ratio = round(float(avg_inhale / avg_exhale), 2)
            else:
                inhale_exhale_ratio = 1.0
        else:
            inhale_exhale_ratio = 0.7  # Normal default

        # --- Signal quality (SNR proxy, 0-1) ---
        if noise_floor > 0:
            breath_energy = float(np.mean(rms[rms > noise_floor * self.noise_gate_factor]))
            if np.isnan(breath_energy):
                breath_energy = float(np.mean(rms))
            snr = breath_energy / noise_floor
            signal_quality = round(min(1.0, snr / 10.0), 2)  # Normalize: SNR 10 = quality 1.0
        else:
            signal_quality = 0.8  # Good default if noise floor is zero

        # --- Dominant frequency ---
        try:
            # Power spectral density of filtered signal
            freqs = np.fft.rfftfreq(len(raw_signal), 1.0 / self.sample_rate)
            psd = np.abs(np.fft.rfft(raw_signal)) ** 2

            # Only look in breath band (100-1000Hz)
            breath_mask = (freqs >= 100) & (freqs <= 1000)
            if np.any(breath_mask):
                breath_psd = psd[breath_mask]
                breath_freqs = freqs[breath_mask]
                dominant_frequency = round(float(breath_freqs[np.argmax(breath_psd)]), 1)
            else:
                dominant_frequency = 400.0
        except Exception:
            dominant_frequency = 400.0

        # --- Intensity classification (refined with real metrics) ---
        intensity = self._classify_intensity(respiratory_rate, volume, breath_regularity)

        return {
            'volume': round(volume, 1),
            'silence_percent': silence_percent,
            'respiratory_rate': respiratory_rate,
            'breath_regularity': breath_regularity,
            'inhale_exhale_ratio': inhale_exhale_ratio,
            'signal_quality': signal_quality,
            'dominant_frequency': dominant_frequency,
            'intensity': intensity,
        }

    def _classify_intensity(self, respiratory_rate: float, volume: float,
                            breath_regularity: float) -> str:
        """Classify workout intensity based on real breath metrics."""
        # Critical: very high respiratory rate OR very loud + irregular
        if respiratory_rate > 40 or (volume > 70 and breath_regularity < 0.3):
            return "critical"
        # Intense: elevated rate or volume
        elif respiratory_rate > 25 or volume > 50:
            return "intense"
        # Moderate: normal exercise range
        elif respiratory_rate > 15 or volume > 25:
            return "moderate"
        # Calm: resting or light activity
        else:
            return "calm"

    # ============================================
    # FALLBACK
    # ============================================

    def _default_analysis(self) -> dict:
        """Return safe default analysis when processing fails."""
        return {
            "silence": 50.0,
            "volume": 30.0,
            "tempo": 15.0,
            "intensity": "moderate",
            "duration": 2.0,
            "breath_phases": [],
            "respiratory_rate": 15.0,
            "breath_regularity": 0.5,
            "inhale_exhale_ratio": 0.7,
            "signal_quality": 0.0,
            "dominant_frequency": 400.0,
        }
