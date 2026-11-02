"""Procedural raster artwork and ffmpeg media steps.

The painter draws a few held intervals and the open rests between them, plus
a small keyboard. Wide and square frames are different compositions. It is an
illustration of economical piano voicing, not a photograph of a session or
of performers.

DejaVu Sans Bold rasterizes the disclosure on the film and the poster. The
font file is not shipped. The poster adds only the line "preview, not master".
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ON_PICTURE = "preview, not master"


def _clamp(value: int) -> int:
    return 0 if value < 0 else 255 if value > 255 else value


def paint(width: int, height: int, framing: str) -> bytes:
    pixels = bytearray(width * height * 3)
    ivory = (223, 230, 226)
    ink = (18, 28, 32)
    copper = (214, 132, 78)
    sage = (118, 156, 142)

    def fill(x0, y0, x1, y1, color):
        x0 = 0 if x0 < 0 else x0
        y0 = 0 if y0 < 0 else y0
        x1 = width if x1 > width else x1
        y1 = height if y1 > height else y1
        red, green, blue = color
        for y in range(y0, y1):
            row = y * width * 3
            for x in range(x0, x1):
                pixels[row + x * 3] = red
                pixels[row + x * 3 + 1] = green
                pixels[row + x * 3 + 2] = blue

    for y in range(height):
        shade = y / max(1, height - 1)
        red = int(16 + 14 * shade)
        green = int(28 + 16 * shade)
        blue = int(34 + 12 * shade)
        row = y * width * 3
        for x in range(width):
            pixels[row + x * 3] = red
            pixels[row + x * 3 + 1] = green
            pixels[row + x * 3 + 2] = blue

    def holds(rects):
        for x0, y0, x1, y1 in rects:
            fill(x0, y0, x1, y1, copper)

    def keys_horizontal(x0, x1, y0, y1, count):
        span = x1 - x0
        key_w = span // count
        for index in range(count):
            left = x0 + index * key_w
            fill(left + 1, y0, left + key_w - 2, y1, ivory)
        for index in range(count - 1):
            if index % 7 in (0, 1, 3, 4, 5):
                left = x0 + (index + 1) * key_w - key_w // 5
                fill(left, y0, left + key_w // 3, y0 + (y1 - y0) * 3 // 5, ink)

    def keys_vertical(x0, x1, y0, y1, count):
        span = y1 - y0
        key_h = span // count
        for index in range(count):
            top = y0 + index * key_h
            fill(x0, top + 1, x1, top + key_h - 2, ivory)
        for index in range(count - 1):
            if index % 7 in (0, 1, 3, 4, 5):
                top = y0 + (index + 1) * key_h - key_h // 5
                fill(x0, top, x0 + (x1 - x0) * 3 // 5, top + key_h // 3, ink)

    if framing == "wide":
        holds([
            (int(width * 0.08), int(height * 0.18), int(width * 0.30), int(height * 0.28)),
            (int(width * 0.08), int(height * 0.34), int(width * 0.22), int(height * 0.44)),
            (int(width * 0.66), int(height * 0.22), int(width * 0.90), int(height * 0.32)),
            (int(width * 0.72), int(height * 0.40), int(width * 0.88), int(height * 0.50)),
        ])
        gap_y = int(height * 0.48)
        for index in range(6):
            x = int(width * (0.36 + index * 0.04))
            fill(x, gap_y, x + 10, gap_y + 4, sage)
        keys_horizontal(int(width * 0.08), int(width * 0.92), int(height * 0.66), int(height * 0.88), 14)
    else:
        holds([
            (int(width * 0.08), int(height * 0.12), int(width * 0.42), int(height * 0.20)),
            (int(width * 0.08), int(height * 0.28), int(width * 0.28), int(height * 0.36)),
            (int(width * 0.10), int(height * 0.70), int(width * 0.36), int(height * 0.78)),
        ])
        rest_x = int(width * 0.18)
        for index in range(5):
            y = int(height * (0.44 + index * 0.04))
            fill(rest_x, y, rest_x + 28, y + 3, sage)
        keys_vertical(int(width * 0.62), int(width * 0.90), int(height * 0.12), int(height * 0.88), 8)
    return bytes(pixels)


def write_ppm(path: Path, width: int, height: int, rgb: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + rgb)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            + " ".join(command)
            + "\n"
            + completed.stderr[-2000:]
        )


def ppm_to_jpeg(ppm: Path, jpeg: Path, quality: int = 3) -> None:
    jpeg.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(ppm), "-frames:v", "1", "-q:v", str(quality), str(jpeg)])


def draw_disclosure(source: Path, dest: Path, textfile: Path) -> list[str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y", "-i", str(source),
        "-vf",
        (
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-frames:v", "1",
        "-q:v", "3",
        str(dest),
    ]
    run(command)
    return command


def encode_mp3(wav: Path, mp3: Path) -> list[str]:
    mp3.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-i", str(wav),
        "-codec:a", "libmp3lame", "-b:a", "192k",
        str(mp3),
    ]
    run(command)
    return command


def encode_film(plate: Path, mp3: Path, mp4: Path, textfile: Path, duration: str) -> list[str]:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "24", "-i", str(plate),
        "-i", str(mp3),
        "-t", duration,
        "-vf",
        (
            "scale=1280:720,"
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-r", "24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        str(mp4),
    ]
    run(command)
    return command


def derive_social(hero: Path, square: Path, portrait: Path, card: Path) -> dict[str, list[str]]:
    portrait.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    portrait_cmd = [
        "ffmpeg", "-y", "-i", str(square),
        "-vf", "crop=864:1080:108:0,scale=1080:1350",
        "-q:v", "3",
        str(portrait),
    ]
    card_cmd = [
        "ffmpeg", "-y", "-i", str(hero),
        "-vf", "scale=1600:900",
        "-q:v", "3",
        str(card),
    ]
    run(portrait_cmd)
    run(card_cmd)
    return {"portrait": portrait_cmd, "card": card_cmd}
