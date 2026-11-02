"""Original emotional piano progressions.

Tempos, bar counts, and collections are fixed before any note is written.
Study 01 is 8 bars at 72 BPM so its full container is the preview and lands
between 10 and 40 seconds. The piano file is the core part. The inner voice
is a separate reference file and is not copied into the piano.

No pedal is encoded. Holds and releases are the written note lengths.
Hand stacks stay within an octave. A leap after less than one bar of space
stays within an octave. A leap after a bar or more of space may reach 16
semitones, which is a reposition during the rest.
"""

from __future__ import annotations

from tools.midi_io import BAR_TICKS_4_4, PPQ, bpm_to_us, effective_bpm

GENERATOR_VERSION = "1.0.0"
PACK_ID = "emotional-piano-progressions"
PACK_NAME = "Emotional Piano Progressions"
BAR = BAR_TICKS_4_4
HAND_SPLIT = 60
SPAN_LIMIT = 12


class Part:
    def __init__(self, study, part_id, role, variation, core, channel, slug, mono, poly, lo, hi):
        self.study = study
        self.part_id = part_id
        self.role = role
        self.variation = variation
        self.core = core
        self.channel = channel
        self.file_slug = slug
        self.monophonic = mono
        self.max_poly = poly
        self.lo = lo
        self.hi = hi
        self.container_ticks = study["bars"] * BAR
        self.notes = []

    def add(self, start, duration, pitch, velocity, departure=False):
        end = start + duration
        if start < 0 or duration <= 0 or end > self.container_ticks:
            raise ValueError(f"{self.part_id} boundary {start}+{duration}")
        if not self.lo <= pitch <= self.hi:
            raise ValueError(f"{self.part_id} pitch {pitch}")
        if not 1 <= velocity <= 127:
            raise ValueError(f"{self.part_id} velocity {velocity}")
        active = 1
        for other in self.notes:
            o0 = other["performed_start"]
            o1 = o0 + other["duration"]
            if start < o1 and o0 < end:
                if other["pitch"] == pitch or self.monophonic:
                    raise ValueError(f"{self.part_id} overlap {pitch}@{start}")
                active += 1
        if active > self.max_poly:
            raise ValueError(f"{self.part_id} poly {active}")
        self.notes.append({
            "nominal_start": start,
            "offset": 0,
            "performed_start": start,
            "duration": duration,
            "pitch": pitch,
            "velocity": velocity,
            "channel": self.channel,
            "departure": departure,
        })

    def finish(self):
        ordered = sorted(self.notes, key=lambda note: (note["performed_start"], note["pitch"]))
        minimum = 8 if self.core else 2
        if len(ordered) < minimum:
            raise ValueError(f"{self.part_id} too few notes")
        for index, note in enumerate(ordered, 1):
            note["id"] = f"{self.part_id}.n{index:04d}"
        return {
            "id": self.part_id,
            "study_id": self.study["id"],
            "slug": self.study["slug"],
            "role": self.role,
            "variation": self.variation,
            "core": self.core,
            "channel": self.channel,
            "file_slug": self.file_slug,
            "path": f"midi/{self.study['slug']}/{self.file_slug}.mid",
            "monophonic": self.monophonic,
            "max_poly": self.max_poly,
            "container_ticks": self.container_ticks,
            "container_bars": self.study["bars"],
            "bpm": self.study["bpm"],
            "tempo_us": self.study["tempo_us"],
            "notes": ordered,
        }


def piano(study, variation):
    return Part(
        study, f"{study['id']}.piano.{variation}", "piano", variation, True, 0,
        f"piano-{variation}", False, 6, 36, 84,
    )


def inner(study, variation):
    return Part(
        study, f"{study['id']}.inner.{variation}", "inner-voice", variation, False, 1,
        f"inner-{variation}", True, 1, 48, 76,
    )


def _norm(notes):
    normalized = []
    for note in notes:
        start = note.get("performed_start", note.get("start"))
        normalized.append({
            "performed_start": start,
            "duration": note["duration"],
            "pitch": note["pitch"],
        })
    return normalized


def _hand(pitch):
    return "lh" if pitch < HAND_SPLIT else "rh"


def review_piano(notes, container):
    """Structural hand check. This does not score emotional quality."""
    errors = []
    norm = _norm(notes)
    attacks = {}
    for note in norm:
        attacks.setdefault(note["performed_start"], []).append(note)
    spans = {"lh": 0, "rh": 0}
    used = {"lh": False, "rh": False}
    max_leap = 0
    for start in sorted(attacks):
        incoming = attacks[start]
        sounding = {"lh": [], "rh": []}
        ended = {"lh": [], "rh": []}
        for note in norm:
            hand = _hand(note["pitch"])
            end = note["performed_start"] + note["duration"]
            if note["performed_start"] < start and end > start:
                sounding[hand].append(note["pitch"])
            elif end <= start:
                ended[hand].append((end, note["pitch"]))
        recent = {}
        for hand in ("lh", "rh"):
            if not ended[hand]:
                recent[hand] = None
                continue
            last_end = max(item[0] for item in ended[hand])
            recent[hand] = (last_end, [pitch for end, pitch in ended[hand] if end == last_end])
        for note in incoming:
            hand = _hand(note["pitch"])
            used[hand] = True
            if sounding[hand]:
                leap = min(abs(note["pitch"] - pitch) for pitch in sounding[hand])
                limit = SPAN_LIMIT
                gap = 0
            elif recent[hand]:
                gap = start - recent[hand][0]
                leap = min(abs(note["pitch"] - pitch) for pitch in recent[hand][1])
                limit = SPAN_LIMIT if gap < BAR else 16
            else:
                continue
            max_leap = max(max_leap, leap)
            if leap > limit:
                errors.append(f"{hand} leap {leap} > {limit} at {start} pitch {note['pitch']}")
        for hand in ("lh", "rh"):
            group = list(sounding[hand])
            group.extend(note["pitch"] for note in incoming if _hand(note["pitch"]) == hand)
            if len(group) > 3:
                errors.append(f"{hand} polyphony {len(group)} at {start}")
            if len(group) >= 2:
                span = max(group) - min(group)
                spans[hand] = max(spans[hand], span)
                if span > SPAN_LIMIT:
                    errors.append(f"{hand} span {span} at {start}")
    intervals = sorted((note["performed_start"], note["performed_start"] + note["duration"]) for note in norm)
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    cursor = 0
    rest = 0
    for start, end in merged:
        rest += start - cursor
        cursor = end
    rest += container - cursor
    if rest < PPQ:
        errors.append(f"breathing room is {rest} ticks, under one quarter")
    stats = {
        "lh_span": spans["lh"],
        "rh_span": spans["rh"],
        "lh_used": used["lh"],
        "rh_used": used["rh"],
        "max_leap": max_leap,
        "rest_ticks": rest,
        "summary": _hand_summary(spans, used, max_leap, rest),
    }
    return stats, errors


def _hand_summary(spans, used, leap, rest):
    def side(name, key):
        if not used[key]:
            return f"{name} rests"
        if spans[key] == 0:
            return f"{name} plays single notes"
        return f"{name} stack {spans[key]} semitones"
    return (
        f"{side('Left hand', 'lh')}. {side('Right hand', 'rh')}. "
        f"Largest leap {leap} semitones. Silent ticks {rest}."
    )


def review_inner(notes, container):
    errors = []
    ordered = sorted(_norm(notes), key=lambda note: note["performed_start"])
    max_leap = 0
    for previous, note in zip(ordered, ordered[1:]):
        previous_end = previous["performed_start"] + previous["duration"]
        if note["performed_start"] < previous_end:
            errors.append("inner voice notes overlap")
        gap = note["performed_start"] - previous_end
        leap = abs(note["pitch"] - previous["pitch"])
        limit = SPAN_LIMIT if gap < BAR else 16
        max_leap = max(max_leap, leap)
        if leap > limit:
            errors.append(f"inner leap {leap} > {limit}")
    if container <= 0:
        errors.append("empty container")
    return {"max_leap": max_leap, "notes": len(ordered)}, errors


def lay(part, rows):
    for row in rows:
        bar_index, tick, duration, pitches, velocity = row[:5]
        departures = row[5] if len(row) > 5 else ()
        if isinstance(pitches, int):
            pitches = (pitches,)
        for pitch in pitches:
            part.add(bar_index * BAR + tick, duration, pitch, velocity, departure=pitch in departures)


def _pair(study):
    return piano(study, "a"), piano(study, "b"), inner(study, "a"), inner(study, "b")


def _s01(study):
    piano_a, piano_b, inner_a, inner_b = _pair(study)
    lay(piano_a, [
        (0, 0, 1920, (45, 52, 60, 64, 69), 76),
        (2, 480, 1920, (41, 48, 60, 65, 69), 74),
        (4, 0, 2880, (48, 55, 64, 67, 72), 82),
        (6, 960, 1440, (50, 57, 65, 69, 74), 78),
        (7, 0, 2400, (45, 52, 60, 64, 69), 90),
    ])
    lay(piano_b, [
        (0, 2880, 720, (57, 60, 64), 70),
        (1, 0, 1440, (52, 60, 67), 72),
        (1, 2400, 480, (64,), 68),
        (2, 1920, 960, (53, 60, 65), 74),
        (3, 960, 1920, (55, 62, 67), 76),
        (4, 480, 480, (48, 64, 72), 80),
        (6, 0, 960, (50, 57, 65), 74),
        (6, 1920, 480, (69,), 70),
        (7, 1440, 960, (45, 64, 69), 86),
    ])
    lay(inner_a, [
        (1, 960, 1920, 64, 60),
        (3, 480, 1440, 69, 58),
        (5, 960, 1920, 67, 62),
    ])
    lay(inner_b, [
        (0, 960, 960, 72, 56),
        (2, 0, 1440, 65, 58),
        (4, 1920, 960, 71, 60),
        (7, 0, 480, 60, 54),
    ])
    return [piano_a, piano_b, inner_a, inner_b]


def _s02(study):
    piano_a, piano_b, inner_a, inner_b = _pair(study)
    lay(piano_a, [
        (0, 0, 960, (38, 74), 72),
        (0, 960, 960, (72,), 70),
        (0, 1920, 960, (69,), 68),
        (2, 480, 2400, (43, 50, 62, 67), 78),
        (3, 2880, 480, (65,), 74),
        (4, 0, 480, (45, 64, 69), 76),
        (4, 1440, 960, (62,), 72),
        (6, 1920, 1440, (48, 55, 64, 67, 72), 80),
        (7, 960, 1920, (50, 57, 65, 69), 88),
    ])
    lay(piano_b, [
        (0, 1920, 1440, (50, 57, 65, 69), 74),
        (1, 0, 2880, (43, 50, 62, 67), 78),
        (3, 960, 960, (45, 64, 69), 76),
        (4, 2880, 720, (48, 60, 67), 74),
        (6, 480, 480, (38, 62), 70),
        (7, 0, 1920, (50, 65, 74), 88),
    ])
    lay(inner_a, [
        (1, 480, 1920, 67, 58),
        (5, 0, 1440, 64, 56),
        (5, 1920, 960, 62, 54),
    ])
    lay(inner_b, [
        (2, 1440, 960, 69, 58),
        (4, 480, 480, 65, 56),
        (7, 2400, 480, 60, 54),
    ])
    return [piano_a, piano_b, inner_a, inner_b]


def _s03(study):
    piano_a, piano_b, inner_a, inner_b = _pair(study)
    lay(piano_a, [
        (0, 0, 1920, (41, 48), 74),
        (0, 1920, 960, (65,), 70),
        (2, 0, 1920, (46, 53), 76),
        (2, 2400, 720, (70,), 72),
        (4, 0, 1440, (48, 55), 78),
        (4, 1920, 960, (67, 72), 80),
        (6, 480, 1440, (43, 50), 76),
        (6, 2400, 960, (67,), 74),
        (7, 0, 2880, (41, 48, 60, 65, 69), 90),
    ])
    lay(piano_b, [
        (0, 960, 480, (69, 72), 70),
        (1, 0, 1920, (50, 57, 65, 69), 76),
        (3, 1440, 1920, (48, 55, 64, 67), 80),
        (5, 0, 960, (65,), 72),
        (6, 2880, 960, (46, 53, 70), 78),
        (7, 960, 1440, (41, 60, 65), 86),
    ])
    lay(inner_a, [
        (1, 0, 1440, 65, 58),
        (3, 960, 960, 70, 60),
        (5, 480, 1440, 67, 56),
    ])
    lay(inner_b, [
        (2, 0, 720, 72, 58),
        (4, 1920, 960, 64, 56),
        (7, 0, 480, 69, 54),
    ])
    return [piano_a, piano_b, inner_a, inner_b]


def _s04(study):
    piano_a, piano_b, inner_a, inner_b = _pair(study)
    lay(piano_a, [
        (0, 0, 480, (64, 67), 74),
        (0, 1920, 480, (59, 62), 72),
        (1, 960, 960, (52, 59), 76),
        (3, 0, 1440, (64, 71), 84),
        (3, 2400, 480, (67,), 78),
    ])
    lay(piano_b, [
        (0, 1440, 240, (76,), 68),
        (0, 1920, 240, (74,), 70),
        (0, 2400, 240, (71,), 72),
        (1, 0, 2880, (40, 47, 64, 67), 80),
        (2, 480, 480, (69,), 74),
        (3, 1920, 960, (59, 66), 84),
    ])
    lay(inner_a, [
        (2, 0, 960, 64, 58),
        (2, 1920, 480, 67, 56),
    ])
    lay(inner_b, [
        (1, 1920, 480, 71, 60),
        (2, 960, 960, 69, 58),
    ])
    return [piano_a, piano_b, inner_a, inner_b]


def _s05(study):
    piano_a, piano_b, inner_a, inner_b = _pair(study)
    lay(piano_a, [
        (0, 0, 1440, (48, 62, 67), 72),
        (0, 1440, 1440, (48, 64, 67), 80),
        (2, 480, 960, (53, 60, 67), 74),
        (2, 1440, 1440, (53, 60, 65, 69), 82),
        (4, 0, 1920, (55, 62, 67), 76),
        (4, 1920, 960, (55, 59, 67), 84),
        (6, 960, 1920, (48, 60, 64, 67), 86),
        (7, 0, 2880, (48, 55, 64, 72), 92),
    ])
    lay(piano_b, [
        (0, 2880, 960, (60, 62, 67), 72),
        (1, 0, 1920, (48, 60, 64, 67), 80),
        (2, 2880, 960, (53, 65, 72), 74),
        (3, 480, 1440, (53, 60, 69), 78),
        (4, 1920, 1440, (55, 71, 74), 82),
        (6, 0, 2880, (48, 64, 67, 72), 88),
    ])
    lay(inner_a, [
        (1, 480, 1440, 64, 58),
        (3, 0, 960, 65, 56),
        (5, 960, 1440, 67, 60),
    ])
    lay(inner_b, [
        (0, 2400, 480, 72, 58),
        (4, 0, 480, 71, 56),
        (6, 0, 960, 60, 54),
    ])
    return [piano_a, piano_b, inner_a, inner_b]


def _s06(study):
    piano_a, piano_b, inner_a, inner_b = _pair(study)
    lay(piano_a, [
        (0, 0, 2880, (43, 50, 62, 65, 70), 74),
        (2, 960, 1920, (48, 55, 60, 63, 67), 78),
        (4, 0, 1440, (43, 50, 62, 67), 76),
        (5, 1920, 1440, (51, 58, 63, 70), 80),
        (7, 480, 2400, (43, 55, 62, 67), 90),
    ])
    lay(piano_b, [
        (0, 480, 1440, (43, 50, 65, 70), 72),
        (2, 1440, 960, (48, 60, 63, 67), 76),
        (4, 240, 1920, (51, 58, 63, 70), 80),
        (6, 960, 480, (43, 62, 67), 74),
        (7, 1920, 1440, (43, 55, 62, 66, 67), 90, (66,)),
    ])
    lay(inner_a, [
        (1, 960, 1920, 65, 58),
        (3, 480, 1440, 63, 56),
        (6, 0, 960, 62, 54),
    ])
    lay(inner_b, [
        (1, 0, 1440, 70, 60),
        (3, 960, 960, 67, 58),
        (5, 480, 1440, 65, 56),
    ])
    return [piano_a, piano_b, inner_a, inner_b]


def _s07(study):
    piano_a, piano_b, inner_a, inner_b = _pair(study)
    lay(piano_a, [
        (0, 0, 960, (46, 53, 58, 65, 70), 76),
        (1, 1440, 720, (43, 50, 62, 67, 74), 78),
        (2, 480, 480, (51, 58, 63, 70), 80),
        (3, 2880, 480, (41, 53, 65, 69), 88),
    ])
    lay(piano_b, [
        (0, 1920, 1440, (58, 65, 69), 74),
        (2, 0, 1920, (51, 63, 67, 70), 80),
        (3, 0, 1920, (69,), 84),
    ])
    lay(inner_a, [
        (0, 1920, 480, 65, 56),
        (1, 0, 480, 67, 58),
        (2, 1440, 480, 70, 60),
    ])
    lay(inner_b, [
        (1, 480, 1440, 69, 58),
        (3, 0, 480, 65, 54),
    ])
    return [piano_a, piano_b, inner_a, inner_b]


def _s08(study):
    piano_a, piano_b, inner_a, inner_b = _pair(study)
    lay(piano_a, [
        (3, 0, 2880, (50, 57, 62, 66, 69), 76),
        (5, 480, 2400, (52, 59, 64, 68, 71), 82),
        (6, 0, 1920, (45, 52, 61, 64, 69), 88),
        (7, 960, 1920, (57, 61, 64, 73), 90),
    ])
    lay(piano_b, [
        (0, 0, 1440, (49, 57, 64, 69), 78),
        (1, 960, 960, (40, 47, 68, 71), 82),
        (2, 0, 2880, (50, 57, 66, 69), 86),
        (7, 0, 960, (69,), 70),
    ])
    lay(inner_a, [
        (0, 960, 1920, 64, 58),
        (1, 0, 1440, 66, 60),
        (2, 480, 960, 61, 56),
        (4, 960, 1440, 68, 58),
    ])
    lay(inner_b, [
        (3, 0, 960, 69, 58),
        (4, 1920, 960, 66, 56),
        (6, 480, 1440, 64, 54),
    ])
    return [piano_a, piano_b, inner_a, inner_b]


BUILDERS = {
    "s01": _s01,
    "s02": _s02,
    "s03": _s03,
    "s04": _s04,
    "s05": _s05,
    "s06": _s06,
    "s07": _s07,
    "s08": _s08,
}


def studies():
    common = {
        "meter": "4/4",
        "bar_ticks": BAR,
        "ppq": PPQ,
        "stochastic_draws": 0,
        "hand_split": HAND_SPLIT,
    }
    rows = [
        {**common, "id": "s01", "slug": "s01-open-thirds", "title": "Open Thirds", "bpm": 72, "bars": 8,
         "tonic": "A", "tonal_reference": "A", "collection_name": "A natural minor",
         "pitch_classes": [9, 11, 0, 2, 4, 5, 7], "departures": [], "seed": 7201,
         "spell": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
         "harmonic_rhythm": "Two bars each of Am and F and C, then one bar of Dm and one bar of Am. The even bars between the first three chords are empty.",
         "changes": ["Am", "F", "C", "Dm", "Am"], "change_bars": [2, 2, 2, 1, 1],
         "phrases": [
             {"name": "Open", "start_bar": 0, "bars": 2},
             {"name": "Shift", "start_bar": 2, "bars": 2},
             {"name": "Lift", "start_bar": 4, "bars": 2},
             {"name": "Return", "start_bar": 6, "bars": 2},
         ],
         "identity": "Variation A holds Am, F, C, Dm, and Am, with a full empty bar after each of the first three chords. Variation B starts on beat 4, fills bars that A leaves empty, and shortens the last chord.",
         "limitations": "Use piano A with inner A, or piano B with inner B. The inner voice is optional. The piano chords are complete without it. No pedal is encoded.",
         "voicing": "Left hand is a fifth or a single bass note under C4. Right hand is a third or a triad from C4 up. Stacks stay within an octave.",
         "layering": "Both hands share the piano file. The inner voice is a separate reference file and is not copied into the piano.",
         "accent": "Cadence velocity is 90. Earlier chords sit between 68 and 82. The variation is not a velocity edit."},
        {**common, "id": "s02", "slug": "s02-falling-alto", "title": "Falling Alto", "bpm": 60, "bars": 8,
         "tonic": "D", "tonal_reference": "D", "collection_name": "D Dorian",
         "pitch_classes": [2, 4, 5, 7, 9, 11, 0], "departures": [], "seed": 6002,
         "spell": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
         "harmonic_rhythm": "Dm, a rest, G for two bars, A, a rest, C, Dm.",
         "changes": ["Dm", "rest", "G", "A", "rest", "C", "Dm"], "change_bars": [1, 1, 2, 1, 1, 1, 1],
         "phrases": [
             {"name": "Fall", "start_bar": 0, "bars": 2},
             {"name": "G", "start_bar": 2, "bars": 2},
             {"name": "A", "start_bar": 4, "bars": 2},
             {"name": "Close", "start_bar": 6, "bars": 2},
         ],
         "identity": "Variation A drops D5, C5, A4, then rests a bar before the chords. Variation B drops that line and places block chords on different beats.",
         "limitations": "The falling line is the motif. It is not a scale run. Inner voice A sits in the empty bars and is not required.",
         "voicing": "The line is one right-hand note at a time. Later chords are a left-hand fifth plus two or three right-hand notes.",
         "layering": "Left-hand notes stay below C4. The inner voice is not merged into those notes.",
         "accent": "The falling line is quieter than the final Dm."},
        {**common, "id": "s03", "slug": "s03-low-fifths", "title": "Low Fifths", "bpm": 54, "bars": 8,
         "tonic": "F", "tonal_reference": "F", "collection_name": "F major",
         "pitch_classes": [5, 7, 9, 10, 0, 2, 4], "departures": [], "seed": 5403,
         "spell": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
         "harmonic_rhythm": "One bar each: F, rest, Bb, rest, C, rest, G, F.",
         "changes": ["F", "rest", "Bb", "rest", "C", "rest", "G", "F"], "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "phrases": [
             {"name": "F", "start_bar": 0, "bars": 2},
             {"name": "Bb", "start_bar": 2, "bars": 2},
             {"name": "C", "start_bar": 4, "bars": 2},
             {"name": "Cadence", "start_bar": 6, "bars": 2},
         ],
         "identity": "Variation A is a left-hand fifth on beat 1 and one right-hand answer later in the bar. Empty bars separate the fifths. Variation B leads with the right hand and reorders the chords.",
         "limitations": "The answer note is not a pedal blur of the fifth. The fifth has already been released, or it is still held only for its written length.",
         "voicing": "Fifths are F-C, Bb-F, C-G, and G-D. The last bar adds a right-hand F triad.",
         "layering": "Until the last bar the hands rarely sound together. That is the written spacing, not a missing track.",
         "accent": "The final F is the loudest chord."},
        {**common, "id": "s04", "slug": "s04-two-note-call", "title": "Two-Note Call", "bpm": 84, "bars": 4,
         "tonic": "E", "tonal_reference": "E", "collection_name": "E natural minor",
         "pitch_classes": [4, 6, 7, 9, 11, 0, 2], "departures": [], "seed": 8404,
         "spell": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
         "harmonic_rhythm": "Em, Em, a full bar of rest, Em.",
         "changes": ["Em", "Em", "rest", "Em"], "change_bars": [1, 1, 1, 1],
         "phrases": [
             {"name": "Call", "start_bar": 0, "bars": 1},
             {"name": "Answer", "start_bar": 1, "bars": 1},
             {"name": "Rest", "start_bar": 2, "bars": 1},
             {"name": "Hold", "start_bar": 3, "bars": 1},
         ],
         "identity": "Variation A speaks in two-note pairs and leaves bar 3 empty. Variation B is a three-note descent into a low fifth, then B and F#.",
         "limitations": "F#4 in variation B is inside E natural minor and is not flagged. The empty bar is the breathing room.",
         "voicing": "Variation A never stacks more than two notes. Variation B opens into a fifth plus a third.",
         "layering": "The inner voice enters only in the gaps. It is not the call.",
         "accent": "The last hold is louder than the opening pair."},
        {**common, "id": "s05", "slug": "s05-suspended-room", "title": "Suspended Room", "bpm": 66, "bars": 8,
         "tonic": "C", "tonal_reference": "C", "collection_name": "C major",
         "pitch_classes": [0, 2, 4, 5, 7, 9, 11], "departures": [], "seed": 6605,
         "spell": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
         "harmonic_rhythm": "C, rest, F, rest, G, rest, then C for two bars.",
         "changes": ["C", "rest", "F", "rest", "G", "rest", "C"], "change_bars": [1, 1, 1, 1, 1, 1, 2],
         "phrases": [
             {"name": "C", "start_bar": 0, "bars": 2},
             {"name": "F", "start_bar": 2, "bars": 2},
             {"name": "G", "start_bar": 4, "bars": 2},
             {"name": "Cadence", "start_bar": 6, "bars": 2},
         ],
         "identity": "Variation A states a suspension and resolves it in the same bar, then rests the next bar. Variation B delays the first suspension until beat 4 and leaves the last bar empty.",
         "limitations": "The resolution is a new written chord. It does not depend on a pedal to hold the first chord through the second.",
         "voicing": "Suspensions are D over C, G over F, and D over G. Each resolves by a step of one or two semitones.",
         "layering": "Inner voice A uses the rest bars. It does not double the suspension.",
         "accent": "The resolved chord is louder than the suspension that precedes it."},
        {**common, "id": "s06", "slug": "s06-plagal-space", "title": "Plagal Space", "bpm": 50, "bars": 8,
         "tonic": "G", "tonal_reference": "G", "collection_name": "G natural minor",
         "pitch_classes": [7, 9, 10, 0, 2, 3, 5],
         "departures": ["Variation B, last bar, F#4 (66) is outside G natural minor. G and D in that chord stay in the set and are not flagged."],
         "seed": 5006,
         "spell": ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
         "harmonic_rhythm": "Gm, rest, Cm, rest, Gm, Eb, rest, Gm. Variation B ends on a G chord with F#.",
         "changes": ["Gm", "rest", "Cm", "rest", "Gm", "Eb", "rest", "Gm"], "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "phrases": [
             {"name": "Gm", "start_bar": 0, "bars": 2},
             {"name": "Cm", "start_bar": 2, "bars": 2},
             {"name": "Eb", "start_bar": 4, "bars": 2},
             {"name": "Return", "start_bar": 6, "bars": 2},
         ],
         "identity": "Variation A leaves a bar empty between the long chords. Variation B enters off the downbeat. Its last chord adds F#4, and that note alone is flagged.",
         "limitations": "Do not treat the flagged F# as part of G natural minor. The other notes in that chord remain in the set.",
         "voicing": "Open fifths with a right-hand third or seventh. No hand stack is wider than an octave.",
         "layering": "The inner voice moves F, Eb, D or Bb, G, F. It is not in the piano file.",
         "accent": "The last chord is the peak. The offbeat variation is slightly softer."},
        {**common, "id": "s07", "slug": "s07-late-question", "title": "Late Question", "bpm": 80, "bars": 4,
         "tonic": "Bb", "tonal_reference": "Bb", "collection_name": "Bb major",
         "pitch_classes": [10, 0, 2, 3, 5, 7, 9], "departures": [], "seed": 8007,
         "spell": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
         "harmonic_rhythm": "Bb, Gm, Eb, and a short F on beat 4.",
         "changes": ["Bb", "Gm", "Eb", "F"], "change_bars": [1, 1, 1, 1],
         "phrases": [
             {"name": "Bb", "start_bar": 0, "bars": 1},
             {"name": "Gm", "start_bar": 1, "bars": 1},
             {"name": "Eb", "start_bar": 2, "bars": 1},
             {"name": "Question", "start_bar": 3, "bars": 1},
         ],
         "identity": "Variation A gives each chord a short attack and leaves the rest of the bar silent. The last chord arrives on beat 4 and does not resolve. Variation B rests the second bar and ends on a single A.",
         "limitations": "The question is the unresolved F, or the single A in variation B. Neither file adds a Bb cadence.",
         "voicing": "Bb, Gm, and Eb are five, five, and four notes. The question is four notes, or one note in variation B.",
         "layering": "Inner voice answers in the gaps. It is not a resolution.",
         "accent": "The late F is louder than the opening Bb even though it is shorter."},
        {**common, "id": "s08", "slug": "s08-cadence-room", "title": "Cadence Room", "bpm": 58, "bars": 8,
         "tonic": "A", "tonal_reference": "A", "collection_name": "A major",
         "pitch_classes": [9, 11, 1, 2, 4, 6, 8], "departures": [], "seed": 5808,
         "spell": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
         "harmonic_rhythm": "Three bars of rest, D, a bar of rest, E, A, A. Variation B states A, E, D first.",
         "changes": ["rest", "D", "rest", "E", "A", "A"], "change_bars": [3, 1, 1, 1, 1, 1],
         "phrases": [
             {"name": "Wait", "start_bar": 0, "bars": 3},
             {"name": "D", "start_bar": 3, "bars": 1},
             {"name": "E", "start_bar": 4, "bars": 2},
             {"name": "A", "start_bar": 6, "bars": 2},
         ],
         "identity": "Variation A is silent for three bars, then moves D, E, A. Variation B states A, E, and D at the start and leaves the next four bars empty except one quiet A at the end.",
         "limitations": "The opening silence is the phrase. It is not a missing file. C# and G# are inside A major and are not flagged.",
         "voicing": "D, E, and A are written as fifth plus third, within an octave in each hand.",
         "layering": "Inner voice A sings through the opening rest. It is still a separate reference.",
         "accent": "The A after the dominant is louder than the D that begins the cadence."},
    ]
    for row in rows:
        if not isinstance(row["bpm"], int) or isinstance(row["bpm"], bool) or not 50 <= row["bpm"] <= 90:
            raise ValueError(row["bpm"])
        if row["bars"] not in (4, 8):
            raise ValueError(row["id"])
        if sum(row["change_bars"]) != row["bars"] or len(row["change_bars"]) != len(row["changes"]):
            raise ValueError(row["id"] + " changes")
        if sum(item["bars"] for item in row["phrases"]) != row["bars"]:
            raise ValueError(row["id"] + " phrases")
        if len(set(row["pitch_classes"])) != 7:
            raise ValueError(row["id"] + " collection")
        row["tempo_us"] = bpm_to_us(row["bpm"])
        row["effective_bpm"] = effective_bpm(row["tempo_us"])
        row["planned_seconds"] = row["bars"] * 4 * row["tempo_us"] / 1_000_000
        nominal = row["bars"] * 4 * 60 / row["bpm"]
        if row["id"] == "s01" and not 10 <= nominal <= 40:
            raise ValueError(f"study 01 preview {nominal}")
        if row["id"] == "s01" and not 10 <= row["planned_seconds"] <= 40:
            raise ValueError(f"study 01 encoded preview {row['planned_seconds']}")
    return rows


def _signature(notes):
    return tuple(sorted(
        (note["performed_start"], note["pitch"], note["duration"]) for note in notes
    ))


def _attack_tuple(notes):
    ordered = sorted(notes, key=lambda note: (note["performed_start"], note["pitch"]))
    return tuple(note["performed_start"] for note in ordered)


def _event_set(notes):
    return {(note["performed_start"], note["pitch"], note["duration"]) for note in notes}


def assert_collections(catalog_studies, parts):
    allowed = {study["id"]: set(study["pitch_classes"]) for study in catalog_studies}
    flagged = []
    for part in parts:
        pool = allowed[part["study_id"]]
        for note in part["notes"]:
            inside = (note["pitch"] % 12) in pool
            if note["departure"] and inside:
                raise ValueError(f"{part['id']} departure {note['pitch']} is inside the collection")
            if note["departure"] and not inside:
                flagged.append((part["id"], note["pitch"]))
            if not note["departure"] and not inside:
                raise ValueError(f"{part['id']} note {note['pitch']} left the collection")
    if flagged != [("s06.piano.b", 66)]:
        raise ValueError(f"departure flags {flagged}")


def assert_identities(parts):
    pianos = [part for part in parts if part["role"] == "piano"]
    by_study = {}
    for part in pianos:
        by_study.setdefault(part["study_id"], {})[part["variation"]] = part
    attacks = {}
    report = []
    for study_id, variations in by_study.items():
        if _signature(variations["a"]["notes"]) == _signature(variations["b"]["notes"]):
            raise ValueError(f"{study_id} variations match in start, pitch, and duration")
        attack = _attack_tuple(variations["a"]["notes"])
        if attack in attacks:
            raise ValueError(f"{study_id} variation A attack times repeat {attacks[attack]}")
        attacks[attack] = study_id
        report.append({
            "study_id": study_id,
            "a": len(variations["a"]["notes"]),
            "b": len(variations["b"]["notes"]),
            "a_attacks": len(set(attack)),
        })
    grouped = {}
    for part in parts:
        grouped.setdefault((part["study_id"], part["variation"]), {})[part["role"]] = part
    for key, roles in grouped.items():
        shared = _event_set(roles["piano"]["notes"]) & _event_set(roles["inner-voice"]["notes"])
        if shared:
            raise ValueError(f"{key} inner voice duplicates piano events")
    return {
        "studies": report,
        "method": (
            "Piano A and B differ in start, pitch, or duration, not velocity alone. "
            "Variation A attack-time tuples are unique across the eight studies. "
            "Departures are flagged only outside the pitch-class set."
        ),
    }


def compose():
    catalog_studies = studies()
    parts = []
    hands = {}
    for study in catalog_studies:
        for part in BUILDERS[study["id"]](study):
            finished = part.finish()
            if finished["role"] == "piano":
                stats, problems = review_piano(finished["notes"], finished["container_ticks"])
                if problems:
                    raise ValueError(finished["id"] + ": " + "; ".join(problems))
                hands.setdefault(finished["study_id"], {})[finished["variation"]] = stats
            else:
                _stats, problems = review_inner(finished["notes"], finished["container_ticks"])
                if problems:
                    raise ValueError(finished["id"] + ": " + "; ".join(problems))
            parts.append(finished)
    assert_collections(catalog_studies, parts)
    identity = assert_identities(parts)
    for study in catalog_studies:
        pair = hands[study["id"]]
        study["hand_span"] = {"a": pair["a"], "b": pair["b"]}
        study["hand_review"] = f"Variation A: {pair['a']['summary']} Variation B: {pair['b']['summary']}"
    core = [part for part in parts if part["core"]]
    refs = [part for part in parts if not part["core"]]
    if len(core) != 16 or len(refs) != 16:
        raise ValueError((len(core), len(refs)))
    if any(part["role"] != "piano" for part in core):
        raise ValueError("core role")
    if any(part["role"] != "inner-voice" for part in refs):
        raise ValueError("reference role")
    preview = next(study for study in catalog_studies if study["id"] == "s01")
    arrangement = {
        "id": "arrangement-preview-s01a",
        "path": "midi/arrangement.mid",
        "format": 1,
        "container_ticks": preview["bars"] * BAR,
        "container_bars": preview["bars"],
        "bpm": preview["bpm"],
        "tempo_us": preview["tempo_us"],
        "meter": "4/4",
        "description": (
            "Study 01 variation A, the full 8-bar container. Piano and inner voice "
            "are separate tracks. The inner voice is not inside the piano file."
        ),
        "tracks": [
            {"name": "Conductor", "source_part": None, "channel": None},
            {"name": "Piano", "source_part": "s01.piano.a", "channel": 0},
            {"name": "Inner Voice", "source_part": "s01.inner.a", "channel": 1},
        ],
    }
    catalog = {
        "pack_id": PACK_ID,
        "pack_name": PACK_NAME,
        "catalog_version": GENERATOR_VERSION,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "meter": {"numerator": 4, "denominator": 4, "bar_ticks": BAR},
        "pitched_range": [36, 84],
        "c4": 60,
        "hand_split": HAND_SPLIT,
        "span_limit_semitones": SPAN_LIMIT,
        "note_policy": "Note-only MIDI. No pedal, no controller, and no program change is encoded.",
        "microtiming": "offset is 0; performed_start = nominal_start",
        "stochastic_draws": 0,
        "seed_meaning": "Seeds identify studies. Nothing is random.",
        "length_plan": (
            "Container lengths and integer tempos were chosen before the notes. "
            "Study 01 is 8 bars at 72 BPM so the full container is the preview. "
            "seconds = bars * 4 * 60 / BPM. 8 bars at 72 BPM is 26.7 seconds."
        ),
        "core_part_count": len(core),
        "reference_part_count": len(refs),
        "range_statement": (
            "Piano uses MIDI 36 to 84, at most six notes at once, and at most three in one hand. "
            "A simultaneous stack in one hand stays within 12 semitones. "
            "Notes below 60 are the left hand. Notes from 60 up are the right hand. "
            "The inner voice is monophonic, MIDI 48 to 76, reference-only, and is not part of the core count."
        ),
        "pedal_statement": (
            "No pedal is encoded. Each chord is held only for its written duration and then released. "
            "The writing stays coherent without an undocumented sustain pedal."
        ),
        "emotion_statement": "Emotional quality is a compositional aim. It is not an automated validation result.",
        "studies": [{key: study[key] for key in (
            "id", "slug", "title", "bpm", "tempo_us", "effective_bpm", "bars", "planned_seconds",
            "meter", "bar_ticks", "tonic", "tonal_reference", "collection_name", "pitch_classes",
            "departures", "seed", "spell", "harmonic_rhythm", "changes", "change_bars", "phrases",
            "identity", "limitations", "voicing", "layering", "accent", "hand_split",
            "hand_review", "hand_span", "stochastic_draws",
        )} for study in catalog_studies],
        "parts": [{
            "id": part["id"],
            "study_id": part["study_id"],
            "role": part["role"],
            "variation": part["variation"],
            "core": part["core"],
            "channel": part["channel"],
            "path": part["path"],
            "notes": len(part["notes"]),
            "container_bars": part["container_bars"],
            "bpm": part["bpm"],
            "monophonic": part["monophonic"],
        } for part in parts],
        "arrangement": arrangement,
        "preview_part_ids": ["s01.piano.a", "s01.inner.a"],
        "preview_seconds_nominal": preview["bars"] * 4 * 60 / preview["bpm"],
        "preview_seconds_encoded": preview["planned_seconds"],
        "stack_warning": (
            "Use either the combined arrangement or the separate parts. "
            "Do not stack the part files on top of the combined file."
        ),
    }
    score = {
        "pack_id": PACK_ID,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "parts": parts,
        "arrangement": arrangement,
        "identity_check": identity,
    }
    return {"catalog": catalog, "score": score}
