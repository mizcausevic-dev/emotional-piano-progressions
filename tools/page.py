"""Catalog page. Voicings and rests are read from the MIDI files."""

from __future__ import annotations

import html
import json
from pathlib import Path

from tools.screening import piano_frames, render_media
from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING


def write_page(path: Path, catalog: dict, report: dict, preview: dict, film: dict) -> None:
    path.write_text(render_page(catalog, report, preview, film), encoding="utf-8")
    root = path.parent
    path.with_name("media.html").write_text(render_media({
        "pack_name": catalog["pack_name"],
        "subject": (
            "Each still is an economical piano voicing: a few held intervals and the rests between them."
        ),
        "colors": {
            "bg": "#142026",
            "paper": "#e7f0ea",
            "ink": "#142026",
            "accent": "#e0a15a",
            "muted": "#a9bdb4",
        },
        "frames": piano_frames(root),
        "preview_seconds": preview["seconds_encoded"],
        "film_seconds": film["duration_seconds"],
    }), encoding="utf-8")


def _rows(catalog: dict) -> str:
    rows = []
    for part in catalog["parts"]:
        kind = "core" if part["core"] else "inner voice reference"
        rows.append(
            "<tr>"
            f"<td><a href=\"{html.escape(part['path'])}\">{html.escape(part['id'])}</a></td>"
            f"<td>{html.escape(part['role'])}</td>"
            f"<td>{html.escape(part['variation'])}</td>"
            f"<td>{kind}</td>"
            f"<td>{part['bpm']}</td>"
            f"<td>{part['notes']}</td>"
            "</tr>"
        )
    return "".join(rows)


def _map(catalog: dict) -> str:
    blocks = []
    for study in catalog["studies"]:
        items = []
        for part in catalog["parts"]:
            if part["study_id"] != study["id"]:
                continue
            kind = "core" if part["core"] else "reference, not in the core count"
            items.append(
                f"<li><a href=\"{html.escape(part['path'])}\">{html.escape(part['id'])}</a> "
                f"{html.escape(kind)}</li>"
            )
        blocks.append(
            "<section>"
            f"<h3>{html.escape(study['id'])} {html.escape(study['title'])}</h3>"
            f"<ul>{''.join(items)}</ul>"
            "</section>"
        )
    return "".join(blocks)


def render_page(catalog: dict, report: dict, preview: dict, film: dict) -> str:
    payload = {
        "hand_split": catalog["hand_split"],
        "studies": [
            {
                "id": study["id"],
                "title": study["title"],
                "bpm": study["bpm"],
                "bars": study["bars"],
                "seconds": round(study["planned_seconds"], 2),
                "collection": study["collection_name"],
                "tonic": study["tonal_reference"],
                "identity": study["identity"],
                "limitations": study["limitations"],
                "voicing": study["voicing"],
                "layering": study["layering"],
                "accent": study["accent"],
                "departures": study["departures"],
                "harmonic_rhythm": study["harmonic_rhythm"],
                "changes": study["changes"],
                "change_bars": study["change_bars"],
                "phrases": study["phrases"],
                "tempo_us": study["tempo_us"],
                "spell": study["spell"],
                "hand_review": study["hand_review"],
            }
            for study in catalog["studies"]
        ],
        "parts": [
            {
                "id": part["id"],
                "study_id": part["study_id"],
                "role": part["role"],
                "variation": part["variation"],
                "path": part["path"],
                "core": part["core"],
            }
            for part in catalog["parts"]
        ],
    }
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    rules = "".join(f"<li>{html.escape(rule)}</li>" for rule in report["rules"])
    seconds = f"{preview['seconds_encoded']:.2f}"
    film_seconds = f"{film['duration_seconds']:.2f}"
    return TEMPLATE.replace("__DATA__", data).replace("__ROWS__", _rows(catalog)).replace(
        "__MAP__", _map(catalog)
    ).replace("__RULES__", rules).replace("__SECONDS__", seconds).replace(
        "__FILM_SECONDS__", film_seconds
    ).replace("__RANGE__", html.escape(catalog["range_statement"])).replace(
        "__LENGTH__", html.escape(catalog["length_plan"])
    ).replace("__PEDAL__", html.escape(catalog["pedal_statement"])).replace(
        "__EMOTION__", html.escape(catalog["emotion_statement"])
    ).replace("__RESULT__", html.escape(report["result"])).replace(
        "__CORE__", str(catalog["core_part_count"])
    ).replace("__REF__", str(catalog["reference_part_count"])).replace(
        "__WARNING__", WARNING
    ).replace("__PROGRAM__", PROGRAM).replace("__AUDITION__", AUDITION).replace(
        "__PREVIEW_LINE__", PREVIEW_LINE
    ).replace("__ON_PICTURE__", ON_PICTURE).replace("__PUBLICATION__", PUBLICATION)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Emotional Piano Progressions</title>
  <style>
    :root {
      --bg: #142026;
      --paper: #e7f0ea;
      --ink: #142026;
      --accent: #e0a15a;
      --copper: #c56a3a;
      --sage: #6e8f84;
      --muted: #a9bdb4;
      --line: rgba(231, 240, 234, .18);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--paper);
      font-family: Georgia, "Iowan Old Style", Palatino, serif;
      line-height: 1.45;
    }
    a { color: var(--accent); }
    p, h1, h2, h3, li, td, .beat { overflow-wrap: anywhere; }
    button, .meta, .beat, .transport { font-family: ui-monospace, Menlo, Consolas, monospace; }
    header, main { width: min(1120px, calc(100% - 2rem)); margin: 0 auto; }
    header { padding: 22px 0 8px; }
    .nav { display: flex; flex-wrap: wrap; gap: 12px; font-size: .82rem; }
    h1 { font-weight: 500; font-size: clamp(2.1rem, 5vw, 4rem); line-height: .95; margin: 8px 0 12px; }
    h2 { font-weight: 500; font-size: 1.5rem; margin: 0 0 8px; }
    h3 { font-size: 1rem; margin: 0 0 8px; font-weight: 500; }
    .kicker { letter-spacing: .14em; text-transform: uppercase; color: var(--accent); font-size: .75rem; }
    .stage img, .player video, .player audio { display: block; width: 100%; height: auto; background: #000; }
    .stage { margin: 12px 0 16px; }
    .rail, .switch { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
    button {
      border: 1px solid var(--line);
      background: transparent;
      color: var(--paper);
      border-radius: 999px;
      padding: 7px 12px;
      cursor: pointer;
    }
    button[aria-pressed="true"] { background: var(--accent); color: var(--ink); border-color: var(--accent); }
    .board, .inner-board, .map {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 12px 0 18px;
    }
    .bar {
      background: var(--paper);
      color: var(--ink);
      border-radius: 14px;
      padding: 10px;
      min-width: 0;
    }
    .bar.now { outline: 3px solid var(--accent); }
    .beats { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
    .beat { min-height: 3.4rem; border-radius: 8px; padding: 6px; font-size: .78rem; }
    .beat.on { background: #f4efe4; border: 1px solid var(--copper); }
    .beat.rest { background: transparent; border: 1px dashed var(--sage); color: #245246; }
    .inner-board .bar { background: transparent; color: var(--paper); border: 1px solid var(--line); }
    .legend { display: flex; flex-wrap: wrap; gap: 14px; color: var(--muted); font-size: .85rem; }
    .swatch { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
    .meta { color: var(--muted); font-size: .85rem; }
    .chain, .flow { display: flex; flex-wrap: wrap; gap: 8px; list-style: none; padding: 0; }
    .chain li, .flow span { border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; font-size: .82rem; }
    .table-scroll { overflow-x: auto; max-width: 100%; }
    table { width: 100%; border-collapse: collapse; font-size: .82rem; }
    th, td { text-align: left; padding: 7px 6px; border-bottom: 1px solid var(--line); vertical-align: top; }
    section.block { margin: 28px 0; padding-top: 18px; border-top: 1px solid var(--line); }
    .transport { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 8px 0 18px; }
    @media (max-width: 800px) {
      .board, .inner-board, .map { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 420px) {
      .board, .inner-board, .map { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <p class="kicker">Emotional Piano Progressions</p>
    <nav class="nav">
      <a href="#board">Voicings</a>
      <a href="#files">Files</a>
      <a href="#reading">Preview</a>
      <a href="media.html">Stills</a>
      <a href="midi/arrangement.mid">Arrangement</a>
    </nav>
  </header>
  <main>
    <p class="kicker">Eight studies, two piano variations, rests written in</p>
    <h1 id="title">Open Thirds</h1>
    <p id="identity"></p>
    <p class="meta" id="facts"></p>
    <p id="rhythm"></p>
    <p id="voicing"></p>
    <p id="hands"></p>
    <p id="limits"></p>
    <p id="departures"></p>
    <figure class="stage">
      <img src="art/hero.jpg" width="1280" height="720" alt="Illustration of an economical piano voicing: a few held intervals and the rests between them. Not a photograph of a studio or of performers.">
      <figcaption>Illustration of economical piano voicing and rests. Not a photograph of a session or of performers.</figcaption>
    </figure>
    <div class="rail" id="rail"></div>
    <div class="switch">
      <button type="button" id="var-a" aria-pressed="true">Variation A</button>
      <button type="button" id="var-b" aria-pressed="false">Variation B</button>
    </div>
    <div class="board" id="board"></div>
    <p class="legend">
      <span><i class="swatch" style="background:#f4efe4;border:1px solid #c56a3a"></i>sounding voicing</span>
      <span><i class="swatch" style="border:1px dashed #6e8f84"></i>rest</span>
    </p>
    <p class="meta" id="status">Reading the MIDI.</p>
    <div class="transport">
      <button type="button" id="play">Play piano</button>
      <button type="button" id="inner-toggle" aria-pressed="false">Inner voice in playback</button>
      <span id="transport-label">Space plays and stops. J and K change the study.</span>
    </div>
    <h2>Inner voice reference</h2>
    <p>This row is not part of the core count and it is not in the piano file. Empty bars stay marked rest.</p>
    <div class="inner-board" id="inner-board"></div>
    <section class="block" id="plan">
      <h2>Lengths chosen first</h2>
      <p>__LENGTH__</p>
      <p>__RANGE__</p>
      <p>__PEDAL__</p>
      <p>__EMOTION__</p>
    </section>
    <section class="block" id="chain">
      <h2>File contract</h2>
      <ol class="chain">
        <li>Canonical score</li>
        <li>MIDI bytes</li>
        <li>Reopened validation</li>
        <li>MP3 preview</li>
        <li>Film and captions</li>
        <li>Stills</li>
        <li>Social drafts</li>
        <li>This catalog page</li>
      </ol>
    </section>
    <section class="block" id="map">
      <h2>Set map</h2>
      <p class="meta">Piano files are the core. Inner voice files are reference only. A and B are alternatives.</p>
      <div class="map">__MAP__</div>
    </section>
    <section class="block" id="files">
      <h2>Files</h2>
      <p class="meta">Validation __RESULT__. Core __CORE__. Inner voice references __REF__. <a href="midi/validation-Cursor.json">validation report</a> · <a href="catalog/catalog-Cursor.json">catalog</a> · <a href="score/canonical-score-Cursor.json">canonical score</a></p>
      <div class="table-scroll">
        <table>
          <thead><tr><th>Part</th><th>Role</th><th>Var</th><th>Count</th><th>BPM</th><th>Notes</th></tr></thead>
          <tbody>__ROWS__</tbody>
        </table>
      </div>
      <p>__WARNING__</p>
    </section>
    <section class="block player" id="reading">
      <h2>Recorded preview</h2>
      <p class="kicker">Study 01, variation A, all 8 bars</p>
      <p>The MP3 is the piano and the inner voice reference together. It is __SECONDS__ seconds. __PREVIEW_LINE__. The film is __FILM_SECONDS__ seconds and shows __ON_PICTURE__.</p>
      <audio controls preload="metadata" src="preview/preview.mp3"></audio>
      <p><a href="preview/preview.mp3">preview/preview.mp3</a> · <a href="preview/preview-manifest-Cursor.txt">preview manifest</a></p>
      <video controls preload="metadata" poster="film/poster.jpg" width="1280" height="720">
        <source src="film/preview.mp4" type="video/mp4">
        <track kind="captions" src="film/preview.vtt" srclang="en" label="English" default>
      </video>
      <p><a href="film/preview.mp4">film/preview.mp4</a> · <a href="film/preview.vtt">film/preview.vtt</a> · <a href="film/poster.jpg">poster</a></p>
    </section>
    <section class="block">
      <h2>Article draft</h2>
      <p><a href="articles/medium-draft-Cursor.md">Article draft</a> · <a href="articles/medium-paste-Cursor.txt">plain text</a></p>
      <p>__PROGRAM__</p>
      <p>__AUDITION__</p>
      <h2>What the validator checks</h2>
      <ul>__RULES__</ul>
      <p>__PUBLICATION__</p>
    </section>
  </main>
  <script id="pack" type="application/json">__DATA__</script>
  <script>
    const pack = JSON.parse(document.getElementById("pack").textContent);
    const rail = document.getElementById("rail");
    const board = document.getElementById("board");
    const innerBoard = document.getElementById("inner-board");
    const status = document.getElementById("status");
    let studyId = "s01";
    let variation = "a";
    let pianoNotes = [];
    let innerNotes = [];
    let audio = null;
    let playing = false;
    let followId = 0;
    let useInner = false;

    function study() {
      return pack.studies.find((item) => item.id === studyId);
    }
    function pitchName(pitch) {
      return study().spell[pitch % 12] + (Math.floor(pitch / 12) - 1);
    }
    function readVlq(view, offset) {
      let value = 0;
      let byte = 0;
      do {
        byte = view.getUint8(offset);
        offset += 1;
        value = (value << 7) | (byte & 0x7f);
      } while (byte & 0x80);
      return [value, offset];
    }
    function parseMidi(buffer) {
      const view = new DataView(buffer);
      const head = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3));
      if (head !== "MThd" || view.getUint16(12) !== 960) throw new Error("unexpected MIDI header");
      const tracks = view.getUint16(10);
      let offset = 14;
      const notes = [];
      for (let track = 0; track < tracks; track += 1) {
        const mark = String.fromCharCode(view.getUint8(offset), view.getUint8(offset + 1), view.getUint8(offset + 2), view.getUint8(offset + 3));
        if (mark !== "MTrk") throw new Error("missing track");
        const length = view.getUint32(offset + 4);
        offset += 8;
        const end = offset + length;
        let tick = 0;
        let running = 0;
        const open = new Map();
        while (offset < end) {
          let delta;
          [delta, offset] = readVlq(view, offset);
          tick += delta;
          let byte = view.getUint8(offset);
          if (byte >= 0x80) {
            running = byte;
            offset += 1;
          }
          if (running === 0xff) {
            offset += 1;
            let metaLen;
            [metaLen, offset] = readVlq(view, offset);
            offset += metaLen;
            continue;
          }
          const kind = running & 0xf0;
          const data1 = byte < 0x80 ? byte : view.getUint8(offset);
          if (byte >= 0x80) offset += 1;
          let data2 = 0;
          if (kind !== 0xc0 && kind !== 0xd0) {
            data2 = view.getUint8(offset);
            offset += 1;
          }
          const key = (running & 0x0f) + ":" + data1;
          if (kind === 0x90 && data2 > 0) open.set(key, { tick: tick, velocity: data2 });
          else if (kind === 0x80 || (kind === 0x90 && data2 === 0)) {
            const started = open.get(key);
            if (started) {
              notes.push({ pitch: data1, start: started.tick, duration: tick - started.tick, velocity: started.velocity });
              open.delete(key);
            }
          }
        }
      }
      notes.sort((a, b) => a.start - b.start || a.pitch - b.pitch);
      return notes;
    }
    function partPath(role) {
      const found = pack.parts.find((part) => part.study_id === studyId && part.role === role && part.variation === variation);
      if (!found) throw new Error("missing " + role);
      return found.path;
    }
    function changeAt(item, barIndex) {
      let bar = 0;
      for (let index = 0; index < item.changes.length; index += 1) {
        const span = item.change_bars[index];
        if (barIndex < bar + span) return item.changes[index];
        bar += span;
      }
      return "";
    }
    function notesInBeat(notes, barIndex, beat) {
      const start = (barIndex * 4 + beat) * 960;
      const end = start + 960;
      return notes.filter((note) => note.start < end && note.start + note.duration > start);
    }
    function namesFor(notes) {
      const ordered = notes.slice().sort((a, b) => a.pitch - b.pitch || a.start - b.start);
      const seen = new Set();
      const names = [];
      ordered.forEach((note) => {
        const name = pitchName(note.pitch);
        if (!seen.has(name)) {
          seen.add(name);
          names.push(name);
        }
      });
      return names;
    }
    function renderCopy() {
      const item = study();
      document.getElementById("title").textContent = item.title;
      document.getElementById("identity").textContent = item.identity;
      document.getElementById("facts").textContent = item.id + " · " + item.bpm + " BPM · " + item.bars + " bars · " + item.seconds + " s at the encoded tempo · " + item.collection + " · tonic " + item.tonic;
      document.getElementById("rhythm").textContent = item.harmonic_rhythm;
      document.getElementById("voicing").textContent = item.voicing + " " + item.layering;
      document.getElementById("hands").textContent = item.hand_review;
      document.getElementById("limits").textContent = item.limitations + " " + item.accent;
      document.getElementById("departures").textContent = item.departures.length ? item.departures.join(" ") : "No pitch in this study is flagged as a departure.";
      document.getElementById("transport-label").textContent = item.title + " " + variation.toUpperCase() + ". Space plays and stops. J and K change the study.";
      for (const button of rail.querySelectorAll("button")) {
        button.setAttribute("aria-pressed", button.dataset.id === studyId ? "true" : "false");
      }
      document.getElementById("var-a").setAttribute("aria-pressed", variation === "a" ? "true" : "false");
      document.getElementById("var-b").setAttribute("aria-pressed", variation === "b" ? "true" : "false");
    }
    function renderBoard() {
      const item = study();
      board.innerHTML = "";
      innerBoard.innerHTML = "";
      let silent = 0;
      const total = item.bars * 4;
      for (let bar = 0; bar < item.bars; bar += 1) {
        const card = document.createElement("article");
        card.className = "bar";
        card.dataset.bar = String(bar);
        const heading = document.createElement("h3");
        heading.textContent = "Bar " + (bar + 1) + " · " + changeAt(item, bar);
        const beats = document.createElement("ol");
        beats.className = "beats";
        for (let beat = 0; beat < 4; beat += 1) {
          const cell = document.createElement("li");
          const sounding = notesInBeat(pianoNotes, bar, beat);
          if (!sounding.length) {
            cell.className = "beat rest";
            cell.textContent = "rest";
            silent += 1;
          } else {
            cell.className = "beat on";
            cell.textContent = namesFor(sounding).join(" ");
          }
          beats.appendChild(cell);
        }
        card.appendChild(heading);
        card.appendChild(beats);
        board.appendChild(card);
        const innerCard = document.createElement("article");
        innerCard.className = "bar";
        const start = bar * 4 * 960;
        const end = start + 4 * 960;
        const inner = innerNotes.filter((note) => note.start < end && note.start + note.duration > start);
        const label = document.createElement("h3");
        label.textContent = "Bar " + (bar + 1);
        const line = document.createElement("p");
        line.textContent = inner.length ? namesFor(inner).join(" ") : "rest";
        innerCard.appendChild(label);
        innerCard.appendChild(line);
        innerBoard.appendChild(innerCard);
      }
      status.textContent = pianoNotes.length + " piano notes from the MIDI file. " + silent + " of " + total + " beats are rests.";
    }
    function stopPlayback() {
      playing = false;
      cancelAnimationFrame(followId);
      if (audio) audio.close();
      audio = null;
      document.getElementById("play").textContent = "Play piano";
      document.querySelectorAll("#board .bar.now").forEach((node) => node.classList.remove("now"));
    }
    function freq(pitch) {
      return 440 * Math.pow(2, (pitch - 69) / 12);
    }
    function schedule(ctx, note, origin, amount) {
      const item = study();
      const seconds = (tick) => tick / 960 * item.tempo_us / 1000000;
      const when = origin + seconds(note.start);
      const duration = Math.max(0.05, seconds(note.duration));
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq(note.pitch);
      const level = amount * (note.velocity / 110);
      gain.gain.setValueAtTime(0.0001, when);
      gain.gain.exponentialRampToValueAtTime(Math.max(0.0002, level), when + Math.min(0.03, duration * 0.25));
      gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(when);
      osc.stop(when + duration + 0.02);
    }
    function playPiano() {
      if (!pianoNotes.length) return;
      stopPlayback();
      const ctx = new AudioContext();
      audio = ctx;
      playing = true;
      document.getElementById("play").textContent = "Stop";
      const origin = ctx.currentTime + 0.05;
      pianoNotes.forEach((note) => schedule(ctx, note, origin, note.pitch >= pack.hand_split ? 0.06 : 0.04));
      if (useInner) innerNotes.forEach((note) => schedule(ctx, note, origin, 0.03));
      const item = study();
      const container = item.bars * 4 * item.tempo_us / 1000000;
      const follow = () => {
        if (!playing || !audio) return;
        const elapsed = audio.currentTime - origin;
        const tick = elapsed / (item.tempo_us / 1000000) * 960;
        const bar = Math.floor(tick / (4 * 960));
        document.querySelectorAll("#board .bar").forEach((node) => {
          node.classList.toggle("now", Number(node.dataset.bar) === bar);
        });
        if (elapsed < container) followId = requestAnimationFrame(follow);
        else stopPlayback();
      };
      follow();
    }
    async function loadStudy() {
      stopPlayback();
      renderCopy();
      status.textContent = "Reading the MIDI.";
      board.innerHTML = "";
      innerBoard.innerHTML = "";
      try {
        const pianoRes = await fetch(partPath("piano"));
        const innerRes = await fetch(partPath("inner-voice"));
        if (!pianoRes.ok || !innerRes.ok) throw new Error("MIDI request failed");
        pianoNotes = parseMidi(await pianoRes.arrayBuffer());
        innerNotes = parseMidi(await innerRes.arrayBuffer());
        renderBoard();
      } catch (error) {
        pianoNotes = [];
        innerNotes = [];
        status.textContent = "The MIDI did not load. " + error.message;
      }
    }
    function stepStudy(direction) {
      const index = pack.studies.findIndex((item) => item.id === studyId);
      studyId = pack.studies[(index + direction + pack.studies.length) % pack.studies.length].id;
      loadStudy();
    }
    pack.studies.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.id = item.id;
      button.textContent = item.id.slice(1) + " " + item.title;
      button.addEventListener("click", () => { studyId = item.id; loadStudy(); });
      rail.appendChild(button);
    });
    document.getElementById("var-a").addEventListener("click", () => { variation = "a"; loadStudy(); });
    document.getElementById("var-b").addEventListener("click", () => { variation = "b"; loadStudy(); });
    document.getElementById("play").addEventListener("click", () => { if (playing) stopPlayback(); else playPiano(); });
    document.getElementById("inner-toggle").addEventListener("click", () => {
      useInner = !useInner;
      document.getElementById("inner-toggle").setAttribute("aria-pressed", useInner ? "true" : "false");
    });
    window.addEventListener("keydown", (event) => {
      const target = event.target;
      if (target && target.closest && target.closest("input, textarea, video, audio, a, button")) return;
      if (event.repeat) return;
      if (event.code === "Space") {
        event.preventDefault();
        if (playing) stopPlayback();
        else playPiano();
      } else if (event.key === "j" || event.key === "J") stepStudy(-1);
      else if (event.key === "k" || event.key === "K") stepStudy(1);
    });
    loadStudy();
  </script>
</body>
</html>
"""
