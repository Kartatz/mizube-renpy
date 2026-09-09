# mizube-renpy

A native [Ren'Py](https://www.renpy.org) conversion of the Adobe Director 11.5
game **mizube / 水辺** (DLsite RE227368, studio White shuttlecock / 白い羽根, 2018).

This is not an emulator or compatibility layer: the original Director data
files were parsed directly, their media extracted, and the recovered Lingo
scenario converted into Ren'Py script. Ren'Py runs natively on Windows,
macOS, Linux, **Android** (via RAPT) and iOS.

## Contents

- `game/script.rpy` — the recovered scenario: ~2,450 original dialogue lines
  in 19 scenes (from the game's own scene counter `qq1`, click-step order),
  with original sound cues
- `game/images/` — 2,349 original 960x720 animation frames (JPEG), organized
  by original cast (`mov` ... `mov8`)
- `game/audio/` — 154 original sound/music members (MP3, plus OGG
  transcodes of the M4A ones)
- `game/animations.rpy` — auto-generated Ren'Py ATL looping animations for
  the frame sequences
- `tools/to_renpy.py` — the converter that generated this project from the
  original game files (Python, stdlib only; also uses ffmpeg if present)

## Running

Open the project with the Ren'Py 8 SDK (8.5.x) and click Start, or:

    renpy.sh /path/to/mizube-renpy run

An automated smoke test is included (`game/testcases.rpy`):

    renpy.sh /path/to/mizube-renpy test story

## Rebuilding from the original files

    python3 tools/to_renpy.py --game /path/to/RE227368 \
        --scripts /path/to/decompiled-system-scripts \
        --font NotoSansJP.ttf --out mizube-renpy

The `--scripts` directory is produced by
[ProjectorRays](https://github.com/ProjectorRays/ProjectorRays):

    projectorrays decompile system.cxt --dump-scripts -o decompiled

## Licensing

- The game assets (images, audio, dialogue text) are dedicated to the
  public domain by the rights holder — see `DEDICATION.md` (the
  dedication file shipped with the game).
- `game/fonts/` contains Noto Sans JP, licensed under the SIL Open Font
  License — see `game/fonts/OFL.txt`.
- `tools/to_renpy.py` and the generated `.rpy` scripts in this repository
  are provided as-is under the same public-domain dedication that covers
  the game materials.

## Content warning

mizube is an adult (18+) game; the extracted artwork reflects that.
