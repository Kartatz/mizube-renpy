# dirplayer-rs exploration: running the original mizube data directly

Explored 2026-09-10, using dirplayer-rs @ main (GPL-3.0), built with
wasm-pack 0.13.1 / rustc 1.98.1, served through the stock `npm start`
CRA dev app, driven headlessly with Playwright + system Chromium.

## Setup that worked

- Movie: the embedded XFIR/MV93 movie extracted from mizube.exe by
  `tools/extract_movie.py` (`/tmp/opencode/work/movie.cct`), served as
  `movie.dcr` over a CORS-enabled HTTP server
- Casts: the game's `mov*.cct` plus `system.cct`/`cgoto.cct` symlinks
  (dirplayer normalizes external casts to `.cct`) next to the movie
- Result: the app loads it — our format stack is supported:
  - XFIR little-endian RIFX: **supported** (`DirectorFile::read`)
  - MV93 + afterburned FGDM/FGDC: **supported**
  - Director 11.5 (version 1150): **in the version table**
  - D6+ delta-compressed score, 48-byte records, 1006 channels: **supported**
    (the parser even pre-scans actual frame counts)
  - External casts via MCsL: **supported** (fetches `<name>.cct`
    relative to the movie URL)
  - Observed parsing: movie (5,777 chunks) + system.cct (234,687-entry
    key table), cgoto.cct, mov.cct, mov2.cct, mov5.cct, mov6.cct...

## Blocker found: memory scale, not formats

Heap instrumentation (wasm memory byteLength around each cast preload):

| step                          | heap after |
|-------------------------------|-----------|
| movie loaded                  | 81 MB     |
| system.cct (11 MB raw)        | 225 MB    |
| cgoto.cct (29 MB raw)         | 432 MB    |
| mov.cct (60 MB raw)           | 1,206 MB  |
| mov2.cct (74 MB raw)          | 1,924 MB  |
| mov5.cct (51 MB raw)          | 2,485 MB  |
| mov6.cct (61 MB raw)          | **OOM (unreachable trap)** |

Causes, in order of impact:

1. **Every cast preloads eagerly.** `CastManager::preload_casts` loads
   all MCsL entries with preload mode 0/1 at MovieLoaded; our combined
   project ships ~450 MB of casts (most of it other games' content).
2. **Chunk materialization multiplies memory ~3-10x.**
   `get_chunk_data` caches a `Vec<u8>` view per chunk, returns
   `.to_vec()` (a second copy), and `make_chunk` clones again into the
   deserialized `Chunk` (a third). Media/CASt/XMedia chunk readers then
   copy the body byte-by-byte again.
3. Two additional pathologies (fixed below) were found and patched while
   debugging.

## Patches made to the local fork (upstream-able)

All in `/tmp/opencode/dirplayer-rs` (scratch — re-apply as a PR):

1. **`chunks/key_table.rs` + `file.rs` — owner-indexed KEY\* lookups.**
   `get_children_of_chunk` linearly rescanned the entire key table per
   cast member (system.cct = 234,687 entries x 270 members of temporary
   Vecs). Added `by_cast_id: HashMap<u32, Vec<usize>>` built once in
   `from_reader`; both `get_children_of_chunk` and
   `get_script_context_key_entry_for_cast` now use it.
2. **`player/cast_member.rs` — gated a 10x hex-dump.** The XMED X2 text
   member path built a `format!("{:02X} ", b)` String per raw byte
   *unconditionally* before `debug!`. Wrapped in `log_enabled!`.
3. **`chunks/media.rs`, `chunks/cast_member.rs`, `cast_info.rs`,
   `thum.rs`, `effect.rs` — capped hex dumps.** Full-body per-byte hex
   strings (a 3-char String + Vec element per byte, then a join) built
   for whole sound/JPEG/CASt bodies; now gated and capped at 256 bytes.

After these the trap moved from "dump allocation" to genuine exhaustion
(`RawVec<u8>::grow_one` OOM while materializing mov6.cct), proving the
remaining problem is the eager-load x copy-amplification, not formats.

## Paths to a playable result

1. **Data-side (no engine changes): rewrite the MCsL preload flags to
   "when needed"** (mode 3 = lazy; `preload_casts` skips modes >= 3).
   Our tooling can patch the movie chunk in place. Casts then load per
   scene; whether every scene fits under the ~4 GB wasm32 heap needs
   testing (mov2.cct alone adds ~700 MB when materialized).
2. **Data-side: strip the casts to mizube-only members.** We know the
   used-member sets from the score dump (`score-data/score_frames.json`)
   and the wrong-game families (mov4/mov5/mov7/mov8 mostly other titles).
   A `.cct` rebuilder using `tools/to_renpy.py`'s Rifx/Cast classes
   would cut raw data and decoded members proportionally.
3. **Engine-side (upstream PR): lazy member materialization.** Don't
   cache both the view and the deserialized chunk; drop the view after
   `make_chunk`; decode bitmaps on first render. This is the "right"
   fix and matches how real Director streams casts.

## Verdict

dirplayer-rs **can** be the runtime for the original data: every
container/protection/score format in this Director 11.5 game is already
implemented, and the movie + all casts parse. The blocker is memory
scalability with this game's 450 MB combined-project casts — fixable
either by patching preload flags + stripping casts (data-side, no
upstream dependency) or by contributing lazy materialization upstream.
Estimated effort: days, not hours — but no format-level unknowns
remain.


## Update 2 (2026-09-10, session 3): lazy bitmap decode — all 11 casts load

Built on the fork's `mizube-compat` branch (now fork main @ f60e9f9).
Measured with the per-phase heap instrumentation, then fixed in stages:

| fix | heap effect |
|-----|-------------|
| start (post hex-dump fixes) | OOM during cast 6 (~3.5 GB) |
| + lazy bitmap decode (decode on first get_bitmap, header-only registration) | OOM during cast 8 |
| + pending registration stops allocating the pixel plane (new_pending built a Bitmap::new shell — the eager allocation the lazy path was paying) | OOM during cast 9 (mov3) |
| + preload takes (moves) the downloaded file instead of cloning it | OOM during mov4 apply |
| + per-member parse-copy release (chunk children cleared as each member is applied) + post-apply view release | **all 11 casts load: 4094 MB** |

Remaining blockers to first frame:

1. **Animated GIF members decode all frames eagerly at apply** — mov7
   (14 MB raw) costs +564 MB, mov4 similar; ~1 GB of the 4094 MB is
   wrong-game GIF frames. Deferring GIF decode (pending + deferred
   `register_pending`) is the next engine change.
2. Zero headroom: the title frame's first renders need ~100-300 MB of
   decode space. The GIF fix above provides it.

Design notes for the eventual upstream PR: `get_bitmap` became
`&mut self` (decode in place) with `get_bitmap_meta`/`get_bitmap_static`
for read-only contexts; dimension-only call sites were switched to the
meta accessor; the internal-cast path keeps a non-releasing apply
variant (the movie file is immutably borrowed during load).


## Update 3 (2026-09-10, session 4): lazy GIF decode; the remaining wall is raw data size

- **Lazy GIF decode** (fork main @ 2344c0e): GIF members no longer decode
  their whole frame set at cast apply. `BitmapMember::pending_gif` carries
  the raw GIF bytes; the Canvas2D and WebGL2 first-draw paths call
  `gif::ensure_gif_decoded`, which decodes, registers the animation and
  swaps in frame 0. `is_gif_member` reports true for pending members.

- **The remaining blocker is data size, not waste**: mizube's eleven casts
  decompress to ~3-4 GB of 32-bit BITD planes (zlib'd to ~450 MB on disk —
  mov7 alone: 14 MB on disk -> ~580 MB decompressed, 280 members x 2.7 MB).
  The lazy-bitmap pending sources retain the DECOMPRESSED bytes, so all
  casts load at ~4041 MB and the first frame cannot decode (needs ~100 MB
  of headroom).

- **Next step (design)**: keep the pending payloads compressed — carry the
  (file offset, length, zlib GUID) source reference plus the decompressed
  length instead of the inflated bytes, and inflate inside decode_pending.
  This requires the raw file bytes to outlive preload (currently released
  by take_task_result after apply), e.g. a per-cast compressed-slab that
  the pending borrows from. Roughly a day of careful work; everything
  else in the load path is already lazy.
