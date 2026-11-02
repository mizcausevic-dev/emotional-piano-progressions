"""Rewrite MIDI, catalog text, and the page from the score.

Leaves the existing preview, film, and stills in place. Study 01 variation A
is unchanged, so those media files stay the published preview.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.article import markdown, plain_text  # noqa: E402
from tools.audit import run_audit  # noqa: E402
from tools.build_pack import probe, write_identity, write_social  # noqa: E402
from tools.compose import compose  # noqa: E402
from tools.page import write_page  # noqa: E402
from tools.validate import dump_json, validate_tree, write_midi_files  # noqa: E402


def main() -> None:
    data = compose()
    dump_json(ROOT / "catalog" / "catalog-Cursor.json", data["catalog"])
    dump_json(ROOT / "score" / "canonical-score-Cursor.json", data["score"])
    write_midi_files(ROOT, data["score"])
    report = validate_tree(ROOT)
    dump_json(ROOT / "midi" / "validation-Cursor.json", report)
    if report["result"] != "PASS":
        raise SystemExit("MIDI validation failed:\n" + "\n".join(report["errors"]))

    manifest_text = (ROOT / "preview" / "preview-manifest-Cursor.txt").read_text(encoding="utf-8")
    preview = json.loads("\n".join(manifest_text.splitlines()[1:]))
    film = json.loads((ROOT / "film" / "film-manifest-Cursor.json").read_text(encoding="utf-8"))
    write_page(ROOT / "index.html", data["catalog"], report, preview, film)
    write_identity(data["catalog"])
    articles = ROOT / "articles"
    articles.mkdir(exist_ok=True)
    (articles / "medium-draft-Cursor.md").write_text(markdown(), encoding="utf-8")
    (articles / "medium-paste-Cursor.txt").write_text(plain_text(), encoding="utf-8")
    write_social()
    probes = {
        "mp3": probe(ROOT / "preview" / "preview.mp3"),
        "mp4": probe(ROOT / "film" / "preview.mp4"),
    }
    checklist = run_audit(ROOT, probes)
    dump_json(ROOT / "checks" / "artifact-checklist-Cursor.json", checklist)
    print(checklist["result"])
    if checklist["result"] != "PASS":
        raise SystemExit(1)
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    if "G for two bars" in page or "E3 C4 G4" in page:
        raise SystemExit("false chord sentence still in the page")


if __name__ == "__main__":
    main()
