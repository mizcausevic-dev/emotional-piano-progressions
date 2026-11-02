"""Repo-owned preview synthesizer.

This is not a General MIDI soundfont and not a mix engine. It renders the
canonical notes for the preview arrangement. The piano is a sine plus a quiet
triangle. The inner voice is a quieter sine. Both last for the written
duration. A few milliseconds of fade at the written note-off only prevents a
click. It is not a sustain pedal, and no pedal is encoded.

Sample positions are absolute:

    sample = floor(seconds * sample_rate + 0.5)

seconds = tick / 960 * encoded_microseconds_per_quarter / 1_000_000.
Intervals are not accumulated. Sample peak is not a loudness measurement.
"""

from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path

SR = 44100
RENDERER_VERSION = "simple-synth-1.0.0"


def tick_to_sample(tick: int, tempo_us: int, sample_rate: int = SR) -> int:
    seconds = (tick / 960) * (tempo_us / 1_000_000)
    return int(math.floor(seconds * sample_rate + 0.5))


def container_seconds(container_ticks: int, tempo_us: int) -> float:
    return (container_ticks / 960) * (tempo_us / 1_000_000)


def _midi_freq(pitch: int) -> float:
    return 440.0 * (2.0 ** ((pitch - 69) / 12.0))


def _render_tone(mix, note, tempo_us, total, amp_scale, partial):
    start = tick_to_sample(note["performed_start"], tempo_us)
    end = tick_to_sample(note["performed_start"] + note["duration"], tempo_us)
    end = min(total, max(end, start + 1))
    freq = _midi_freq(note["pitch"])
    inc = freq / SR
    phase = 0.0
    tri = 0.0
    amp = (note["velocity"] / 127.0) * amp_scale
    for index in range(start, end):
        phase += inc
        if phase >= 1.0:
            phase -= 1.0
        tri += inc * 2.0
        if tri >= 1.0:
            tri -= 1.0
        sine = math.sin(2.0 * math.pi * phase)
        triangle = 1.0 - 4.0 * abs(tri - 0.5)
        t = (index - start) / SR
        remain = (end - index) / SR
        env = 1.0
        if t < 0.02:
            env *= t / 0.02
        if remain < 0.03:
            env *= remain / 0.03
        mix[index] += int((sine + triangle * partial) * env * amp)


def render_preview(parts: list[dict], tempo_us: int, container_ticks: int, wav_path: Path) -> dict:
    total = tick_to_sample(container_ticks, tempo_us)
    mix = array("i", [0]) * total

    def add_piano(note):
        _render_tone(mix, note, tempo_us, total, 4600.0, 0.16)

    def add_inner(note):
        _render_tone(mix, note, tempo_us, total, 2200.0, 0.0)

    roles = {
        "piano": add_piano,
        "inner-voice": add_inner,
    }
    rendered = []
    for part in parts:
        voice = roles[part["role"]]
        for note in part["notes"]:
            voice(note)
        rendered.append({"id": part["id"], "role": part["role"], "notes": len(part["notes"])})

    peak = 0
    for sample in mix:
        magnitude = sample if sample >= 0 else -sample
        if magnitude > peak:
            peak = magnitude
    if peak == 0:
        raise RuntimeError("preview mix is silent")
    scale = 1.0 if peak <= 28000 else 28000.0 / peak
    pcm = array("h")
    for sample in mix:
        value = int(sample * scale)
        if value > 32767:
            value = 32767
        elif value < -32768:
            value = -32768
        pcm.append(value)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())
    sample_peak = int(peak * scale)
    return {
        "renderer": RENDERER_VERSION,
        "sample_rate": SR,
        "channels": 1,
        "sample_format": "signed 16-bit little-endian PCM",
        "samples": total,
        "seconds": container_seconds(container_ticks, tempo_us),
        "rounding": "sample = floor(seconds * sample_rate + 0.5), computed from tick 0; intervals are not summed",
        "sample_peak": sample_peak,
        "sample_peak_dbfs": 20.0 * math.log10(sample_peak / 32768.0),
        "sample_peak_note": "This is a sample peak of the integer mix after scaling. It is not a loudness measurement and it is not a true-peak measurement.",
        "voices": rendered,
        "mapping": {
            "piano": "sine plus a quiet triangle, held for the written duration, with a few milliseconds of fade at the note-off",
            "inner-voice": "quieter sine at the written pitch, held for the written duration, with the same short fade",
        },
        "mapping_note": (
            "These voices are preview mappings. They are not encoded in the MIDI file. "
            "The fade is click prevention at the written release. It is not a sustain pedal."
        ),
    }
