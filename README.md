# Emotional Piano Progressions

Original note-only MIDI studies of economical piano voicing. Eight studies, two variations of the piano. The inner voice is cataloged separately and is not part of the core count. It is not merged into the piano files.

Container lengths and tempos were chosen before the notes. Study 01 is 8 bars at 72 BPM. seconds = bars * 4 * 60 / BPM, so that full container is about 26.7 seconds and it is the preview. A 16-bar study at these tempos would run past 40 seconds, so this pack uses 4-bar and 8-bar containers.

This repository is the pack. The GitHub repository is https://github.com/mizcausevic-dev/emotional-piano-progressions and it is public. The catalog page is https://mizcausevic-dev.github.io/emotional-piano-progressions/ .

## What you can open

- `index.html` is the file catalog. Piano voicings and rests are read from the MIDI bytes. Space plays and stops. J and K change the study.
- `media.html` is the stills page. The film sits under the pictures.
- `midi/arrangement.mid` is a Format 1 preview arrangement of study 01, variation A: piano and inner voice reference.
- Individual Format 0 parts live under `midi/`.
- `midi/validation-Cursor.json` is the report from reopening those exact bytes.
- `preview/preview.mp3` is the primary music preview. It is 26.667 seconds in the encoded file. preview, not a master.
- `film/preview.mp4` and `film/preview.vtt` are the film. On-picture and caption text is `preview, not master`.
- `art/hero.jpg` is a 1280x720 illustration. `art/square.jpg` is 1080x1080. Neither is a photograph.

Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.

## Studies

- s01 Open Thirds: 72 BPM, 8 bars, 26.67 seconds at the encoded tempo, A natural minor, tonic reference A.
- s02 Falling Alto: 60 BPM, 8 bars, 32.00 seconds at the encoded tempo, D Dorian, tonic reference D.
- s03 Low Fifths: 54 BPM, 8 bars, 35.56 seconds at the encoded tempo, F major, tonic reference F.
- s04 Two-Note Call: 84 BPM, 4 bars, 11.43 seconds at the encoded tempo, E natural minor, tonic reference E.
- s05 Suspended Room: 66 BPM, 8 bars, 29.09 seconds at the encoded tempo, C major, tonic reference C.
- s06 Plagal Space: 50 BPM, 8 bars, 38.40 seconds at the encoded tempo, G natural minor, tonic reference G.
- s07 Late Question: 80 BPM, 4 bars, 12.00 seconds at the encoded tempo, Bb major, tonic reference Bb.
- s08 Cadence Room: 58 BPM, 8 bars, 33.10 seconds at the encoded tempo, A major, tonic reference A.

Core files: 16. Reference files: 16.

Piano uses MIDI 36 to 84, at most six notes at once, and at most three in one hand. A simultaneous stack in one hand stays within 12 semitones. Notes below 60 are the left hand. Notes from 60 up are the right hand. The inner voice is monophonic, MIDI 48 to 76, reference-only, and is not part of the core count. C4 is 60. PPQ is 960. Meter is 4/4. Offsets are 0. Seeds identify studies and are not random draws. Generator 1.0.0. No pedal is encoded. Each chord is held only for its written duration and then released. The writing stays coherent without an undocumented sustain pedal. Emotional quality is a compositional aim. It is not an automated validation result.

Measured hand spans are in `score/identity-Cursor.md`. A stack wider than 12 semitones is rejected. A leap after less than a bar of space stays within 12 semitones. A leap after a bar or more may reach 16 semitones.

## Preview path

The preview renders the canonical notes for `s01.piano.a` and `s01.inner.a` with `simple-synth-1.0.0`. Tempo authority is the encoded microsecond value in the MIDI, 833333 us per quarter note. Sample positions use `floor(seconds * 44100 + 0.5)` from tick 0. Intervals are not summed. Sample-exact repeating loops at an arbitrary BPM are not promised.

The synth mapping is a sine plus a quiet triangle for the piano and a quieter sine for the inner voice. The fade at the written release is a few milliseconds and is not a sustain pedal. No program changes are encoded. A conventional GM player will normally use its default piano program for pitched channels unless configured otherwise; compatible GM channel 10 percussion is treated separately. Player behavior may vary. The mapping is not encoded in the MIDI.

Encoded MP3 settings: libmp3lame, 192 kbps. Film audio is AAC at 160 kbps re-encoded from that MP3, so the decoded film audio is not byte-identical to the MP3. Film duration probe: 26.667 seconds. MP3 container probe 26.667 seconds. MP4 probe 26.667 seconds. The film ends on a video frame, so it may be slightly shorter than the MP3 container. The music is the same preview, not a different excerpt. The picture is a still illustration with rasterized disclosure text. DejaVu Sans Bold from the build machine supplies the glyphs. The font file is not in this pack.

No human listening audition was performed for this build. A sample peak is recorded in the preview manifest. It is a sample peak of the integer mix. It is not a loudness measurement and it is not a true-peak reading.

## Build

From the repository root, with Python 3.11+ and ffmpeg (libmp3lame, aac, libx264):

```bash
python3 tools/build_pack.py
python3 -m http.server 43141
```

The page is static. It is served with Python's HTTP server so the MIDI and media keep working relative paths. There is no application server and no package install. Standard library only.

`build/` holds the intermediate WAV, the procedural PPM, and the film plate. Those files are gitignored. The delivered audio is the MP3.

## Checks the validator actually runs

File existence, parse, PPQ, tempo, 4/4, end-of-track boundary, note pairing, piano range 36 to 84, inner-voice range 48 to 76, piano polyphony cap of six, monophonic inner voice, hand span within an octave, leap review, variation identity, unique variation A attack times, departure flags against the declared pitch-class set, agreement with the canonical score, and agreement between `arrangement.mid` and the two source files. A negative overlap fixture is written outside the pack and must be rejected. Emotional quality is not one of these checks.

## Drafts and publication

Social captions, the X post, and the Medium article are drafts. They are not access controls. If this repository is public, the drafts are public. Do not treat them as posted to Instagram, X, or Medium.

Prepared repository description: Original note-only MIDI studies of emotional piano progressions, with matched validation and a simple-synth preview.

Prepared topics: midi, piano, composition, music-production, harmony.

No release tag was created. `index.html` keeps its name because players and links depend on it. This page is the file catalog the pack requires.

## Limitations

Variation A and variation B of a study are alternatives. Pair inner voice A with piano A, and inner voice B with piano B. The arrangement is only study 01. Stacking it with the part files doubles those notes. The piano files are playable without the inner voice. These studies are original.
