"""Factual article draft. Not published."""

from __future__ import annotations

from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING

TITLE = "Emotional Piano Progressions is a note-only MIDI study pack"
SUBTITLE = "Eight piano studies with rests, two variations each, and a simple-synth preview that is not a master"
TAGS = ["midi", "piano", "composition", "music-production", "harmony"]
TAG_LINE = "Tags: " + ", ".join(TAGS)

PARAGRAPHS = [
    "DRAFT. " + PUBLICATION,
    TAG_LINE,
    "The pack is eight piano studies in 4/4. Tempos are integers from 50 to 90 BPM. Container lengths were chosen before the notes: six studies are 8 bars and two are 4 bars. Study 01, Open Thirds, is 8 bars at 72 BPM. That full container is the music preview, about 26.7 seconds. Sixteen piano files are the core, two variations for each study. Sixteen inner-voice files are reference only. They are not in the core count and they are not merged into the piano files.",
    "Open Thirds holds Am, F, C, Dm, and Am, with an empty bar after each of the first three chords. Falling Alto drops D, C, A and then answers with chords. Low Fifths is a left-hand fifth plus one right-hand note. Two-Note Call speaks in pairs and leaves a bar empty. Suspended Room resolves a suspension in the same bar, then rests. Plagal Space leaves a bar empty between Gm, Cm, and Eb. Late Question puts its last chord on beat 4. Cadence Room is silent for three bars, then moves D, E, A. Variation B of each study changes the attack, the pitch, or the duration. A velocity edit alone does not count.",
    "Piano notes stay between MIDI 36 and 84. One hand stacks at most three notes, and that stack stays within an octave, 12 semitones. Notes below 60 are the left hand. Notes from 60 up are the right hand. The inner voice is monophonic and stays between 48 and 76. C4 is 60. The resolution is 960 ticks per quarter note. There is no timing offset. No pedal is encoded. Each chord ends at its written note-off, so the progression stays coherent without an undocumented sustain pedal. Emotional quality is a compositional aim. It is not an automated validation result.",
    PROGRAM,
    "The preview synth uses a sine plus a quiet triangle for the piano and a quieter sine for the inner voice. A few milliseconds of fade at the written release only prevents a click. That mapping is documented. It is not a program change and it is not a sustain pedal.",
    "The primary preview is study 01, Open Thirds, variation A, for all 8 bars: the piano file and the inner-voice reference together. The other studies are in the MIDI and are not in that audio file. "
    + PREVIEW_LINE
    + ". The film takes its audio from that preview file and shows the words "
    + ON_PICTURE
    + " on the picture and in the WebVTT captions.",
    AUDITION
    + " The validator reopened the MIDI bytes and compared them with the canonical score. It also checked hand span, leaps, rests, and that variation A and variation B differ in start, pitch, or duration. That is a structural check. The sample peak written beside the preview is the peak of the integer mix. It is not a loudness measurement and it is not a true-peak reading.",
    "The stills are procedural illustrations of an economical piano voicing: a few held intervals and the rests between them, with a small keyboard. They are not photographs of a session or of performers.",
    "When you use the files, use either the combined arrangement or the separate parts. " + WARNING,
    "Call to action: the MIDI, the matched report, and the preview belong together. Do not publish this draft to Medium, Instagram, or X from the draft files alone.",
]


def markdown() -> str:
    body = "\n\n".join(PARAGRAPHS)
    return f"# {TITLE}\n\n{SUBTITLE}\n\n{body}\n"


def plain_text() -> str:
    lines = [TITLE, "", SUBTITLE, "", *PARAGRAPHS, ""]
    return "\n".join(lines) + "\n"
