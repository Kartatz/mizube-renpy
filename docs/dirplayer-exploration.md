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


## Update 4 (2026-09-11): compressed pending sources — the movie BOOTS

Two commits on the fork (d2d205c, 1e16607), full rewrite of the lazy
media path to keep payloads zlib-compressed until first render:

- `PendingBitmap::CompressedBitd` / `CompressedJpegWithAlfa` carry
  (Arc slab, offset, len, compression id) instead of inflated bytes;
  the DirectorFile wraps the raw file bytes in an Arc slab, each
  member's children record their (offset, len) provenance at parse
  time (`child_sources`), and `decode_pending` inflates with flate2 on
  first use.
- The eagerly-decoding `resolve_unresolved_palette_refs` pass at movie
  start switched to `get_bitmap_meta` (pending shells are skipped —
  they carry a BuiltIn palette ref).

Measured: all 11 casts preload in **~1.16 GB** of the 4 GB wasm32 heap
(was: OOM). The movie then BOOTS: live 960x720 canvas, WebGL renderer
active, score loop running (`__dirplayerFrameTempo=12`), React chrome
hidden.

**Current blocker: the playhead holds frame 1.** The opening
title-card frames use the movie's special tempo channel (frames 8/9
hold tempo 248/247 = wait-in-ticks); frame 1 sits at a hold tempo and
neither real canvas clicks nor `mcp_eval_lingo('go 340')` (which
reports success) advance it. Next investigation: dirplayer's
`run_frame_loop` tempo-0/wait-tick semantics and its `go` dispatch —
the frame-1 script member (system 1828) has an empty CASt, so this is
engine-behavior debugging, not format work.

Debug aids added along the way: `window.__dirplayerLogLevel='debug'`
selects the wasm log level pre-load; `window.__dirplayerFrame`
publishes the playhead; `window.__vm` (the app's module handle)
exposes `mcp_eval_lingo` for headless Lingo probes.


## Update 5 (2026-09-11, session 2): THE MOVIE RUNS

The "playhead holds frame 1" mystery had a mundane root: **the LoadMovie
UI's Auto-play checkbox defaults OFF** — `play()` was never called, so
no frame loop ever ran and `go()`'s next_frame sat unconsumed. A new
`window.__vm.dirplayer_playbackState()` probe exposed (is_playing=…) and
settled it in one measurement.

With `play()` invoked (fork @ 626466a):

- **The playhead advances through the original title-card sequence** at
  the authored tempo (frames hold ~247/248 wait-ticks ≈ 4s per card —
  matching the original game's opening observed under Wine), reaching
  frame 9 within ~20s of play on a settled load, and `go(340)` jumps
  to the `startxa` marker exactly as authored.
- `begin_all_sprites` runs; the score's 1506 sprite channels apply.

Remaining issues, in priority order:
1. **The renderer never draws** — the 960x720 canvas stays pure black
   while the frame loop runs (WebGL2 backend; a "GPU stall due to
   ReadPixels" shows activity but no output). Renderer scheduling /
   stage_dirty propagation is the next investigation.
2. **play() takes ~60s to become active** — the init re-parses every
   cast's film-loop scores at play time ("Finished processing 56/15/66/62
   frames" logs) on top of the 21973-frame pre-scan; a settled load +
   play advances within seconds.
3. The headless Auto-play default should be ON (or play() auto-invoked
   post-`whenMovieLoaded`) — one-line app change.

Everything up to the render is now verified working end-to-end: movie
parse, 11 external casts (compressed pending), Xtra declaration handling,
Lingo eval (`mcp_eval_lingo`), the score loop, and the marker table.


## Update 6 (2026-09-11, session 3): THE GAME RENDERS AND PLAYS

Fork @ 1cea090. One-line-class fix with game-changing consequences:

**`player_call_global_handler` routed the global-verb form of async Xtra
instance verbs to the sync handler** (whose stub errors), freezing the
movie at frame 1 the moment mizube's boot script called
`openFile` (FileIO Xtra, reading its save/config data). The method-call
path already checked `has_xtra_instance_async_handler`; the global-verb
path now does too.

With that fix, the FULL original game runs in the browser:

- Boot: the playhead advances through the original title-card tempo
  (frames 1-339), crosses the title menu (`startx` @340), passes the
  `start` marker (@454), and renders the park scene in WebGL — canvas
  mean 169.9, 66% bright content, with the sprite structure visible.
- No script errors trip the debugger; playback state stays
  `playing=true, paused=false` throughout a 2-minute run.
- Heap: ~1.16 GB steady (the compressed-pending work holds).

Remaining knowns before full playability:
1. Input: clicks/keys must reach the movie's event system (the title
   menu needs a click on the four `bn/bv/bm/bg` buttons).
2. Sound: 17 declared Xtras (DirectSound/MacroMix/SWA) were missing —
   audio behavior untested.
3. Frame 1 hold: pre-menu frames include the opening black cards —
   verify the menu actually waits for a click rather than auto-advancing
   (the run crossed 340→454 without input, suggesting either an
   auto-advance or a menu the headless run couldn't see).


## Update 7 (2026-09-11, session 3 end): INTERACTIVE — clicks drive the movie

Verified in the same headless harness: a physical mouse click on the
canvas at the authored `bn` menu-button coordinates (461,458 stage →
621,578 page) was routed into the movie's event system; a script
responded and the playhead JUMPED (frame 461 -> 19948 -> playing
through the opm*/fn_* opening-movie ranges -> 680+). The game is not
merely rendering — it is INTERACTIVE, scripts execute, and marker-based
`go` flow works end-to-end.

The original mizube.exe's data — movie + eleven castLibs + FileIO
boot script — now runs in a stock browser through dirplayer-rs with no
Wine, no Director, and no reimplementation.

Session totals on the fork (igorlira/dirplayer-rs <- Kartatz fork main):
1. KEY* owner index (fixes O(members x entries) scans)
2. Hex-dump gating/capping (per-byte 10x amplification)
3. Heap instrumentation
4. Lazy bitmap decode + borrow model
5. Lazy GIF decode
6. Compressed pending sources (Arc slab + provenance + flate2 on demand)
7. Palette-resolution meta path
8. Log-level selector, playback/frame probes
9. Global-verb async Xtra instance dispatch (the openFile boot freeze)

Next steps, all engine-side now: menu semantics (which button does
what), the 17 audio Xtras, and the tempo-0 click-wait behavior at the
title cards.


## Update 8 (2026-09-11, session 4): menu mapped, frame-694 hold diagnosed

Menu button sweep (fresh run per button, canvas clicked at the authored
coordinates):

| button | stage pos | result |
|-------|----------|--------|
| bn | (461,458) | NEW GAME -> opening movie (19926-20423) -> intro @694 |
| bv | (457,524) | hold @515 (save screen) |
| bm | (455,586) | hold @599 (load screen) |
| bg | (453,642) | hold @457 (menu) |

The New Game path renders the full opening movie then the intro at
frame 694 (park background, EN title "The Blind Spot in the Park"
rendered as text, kurikku click cue, dialogue box) — but clicking
anywhere does not advance, and the frame holds.

**The hold, diagnosed with the extended probe (fork @ 7766133):**
- On entry to 694 the score transition (fade-in) arms a playhead hold;
  the frame oscillates through a re-arm loop (transHold true at every
  sample; the frame script at 695 likely bounces back to 694).
- Frame 694's tempo channel value is 0 — Director's WAIT-FOR-CLICK
  code — which the engine does not implement as a hold; the loop keeps
  cycling instead of parking.
- No sprite on frame 694 has behaviors (in-engine:
  `sprite(47).scriptInstanceList == []`), so the click-advance comes
  from the frame script. The score's script member for 694 is
  system#9 "待機goto frame" — a type-11 SCRIPT member whose body is NOT
  in the cast's KEY* table. The actual bodies live in system.cxt's
  LctX: **1904 Lscr chunks** (verified header: entryCount 1942,
  entriesOffset 96, 96 + 1942*12 = 23400 = exact chunk length; lnam
  section 231986; validCount 1904). The flow handlers are visible in
  the Lscr strings: `start`, `demo`, `help`, `save`, `load`,
  `lookdata` (the marker-look tables), plus 1300+ distinct strings.

**Next steps for playability (all one area: script member -> Lscr
resolution + tempo-0 hold):**
1. Resolve type-11 script members to their Lctx Lscr sections so
   frame scripts like "待機goto frame" execute (wait-for-click loops,
   marker jumps).
2. Implement the tempo-0 = hold-until-click/key playhead semantics.
3. The transition re-arm loop needs the fade to complete via the
   renderer rather than re-arming on each cycle.

## Update 9 — Tempo 247/248 + the frame-694 mystery fully solved; intro is playable

Engine fork commit `451d43c` (on top of `7766133`).

### Tempo channel semantics (definitive)

Full-movie tempo dump (21973 frames): **only 4 frames use mode 248**
(wait for click: 8, 696, 2097, 14691), 101 use 247 (delay N seconds),
155 use 246 (FPS from cue). Entries are **per-frame settings, not
keyframe spans** — the next entry after 248@696 is 247@854, so span
inheritance would demand ~150 clicks to leave the intro (matches
ScummVM, which attaches TempoChannelData to the frame record it
appears in; consecutive 247 entries at 1230/1231 also confirm this).

Implemented in the fork:
- `get_frame_tempo_entry(frame)` — exact-frame entry lookup.
- `begin_all_sprites` arms `tempo_wait_click` (248) and sets
  `delay_until` (247, cue seconds) on frame entry.
- `run_single_frame` holds the tick before exitFrame while armed;
  any mouseUp/KeyDown releases for one advance (set in the
  commands.rs handlers, before script dispatch).
- Normal advance clears both flags; re-entry re-arms.

Verified live: title card 8 holds until click; delay cards 32/56/58
hold 2s/2s/4s; intro gate 696 holds until click.

### Frame 694 — the whole mechanism, decoded

The pin at 694 was **not** a bug: it is the game's design.
- Every ~100ms a **timeout heartbeat** (handlers `tim1`/`tim100`
  present in dozens of system scene scripts) re-anchors the playhead
  with `go fra` (global `fra` = scene anchor frame = 694 during the
  intro). Debug log: `go() called: current_frame=694 datum=694` ~23/s.
- The intro dialogue advance lives in **system script 1053 `mouseUp`**
  (attached to sprite 48 via its member 1798; kurikku icon = ch47):
  - if `_key.keyPressed('s')` → skip: `ssina = 0`,
    `member("main").text = <intro line 1>`, `go the frame + 1`
  - else `ssina = ssina + 1; nt()` and `member("main").text` cycles
    through 4 intro lines; on `ssina == 5`: reset + `go the frame + 1`.
  - 695's exitFrame (system#48): `if pp10 < 3 then pp10 = 4;
    mainsave()` — mainsave has no handler anywhere (silently ignored);
    pass-through requires `pp10 >= 3` which the cycle satisfies.
- 696 is tempo 248 — the wait-click gate into the scene sequence.

End-to-end live trace: 694 (5 dialogue clicks) → 695 → 696 (248 hold)
→ release click → 726 → scene clicks advance 727→745→763→781→799→818→
837→854→862 (~18 frames per card). The intro is now **fully playable**.

### Tooling added

`/tmp/opencode/dp/disasm.py` — Lingo bytecode disassembler for the
system Lctx (D11.5 opcode remap `op >= 0x40 -> 0x40 + op % 0x40`,
operand widths by raw op >= 0xc0/0x80/0x40, extCall/getGlobal name
annotation against the cast Lnam, literal-pool dump incl. strings).
Used to decode: wake (9), exitFrame (48), mouseUp (1053), tim1/tim100
scene heartbeats. Copied to mizube-renpy/tools/lingo_disasm.py.

Also instrumented the mouseUp cast-member-script fallback branch in
commands.rs (was silent through `?`; mouseDown's mirror path logs) —
that's how the dead-looking dispatch was traced to actually running
1053's mouseUp.

### Known-open

- `mainsave` handler referenced by 695's exitFrame does not exist in
  any cast (silently ignored — no crash, pp10 gate still passes).
- The dialogue text field (lib1 m11 "main", sprite ch138) does not
  appear in TEXT_RECT draw logs — the `member("main").text` update
  may not be rendering; needs a look (dialogue might be invisible
  even though the cycle works).
- `wake` (system#9) final block: `if fra == -10000 then qq14 = 0;
  go <const 1>` — the -10000 sentinel path is untested.

## Update 10 — Movie-internal cast members never loaded; the dialogue box now renders

Engine fork commit `e576c41`.

### The bug

`member("main")` — the intro dialogue field — resolved to `#empty`
(number -1). The dialogue click-cycle (behavior 1053's `mouseUp`) ran
perfectly and wrote `member("main").text` four times per intro card,
but every write went to a dummy member and nothing ever appeared.

Root cause: **`apply_cast_def_keep` had no callers.** When
`CastManager::load_from_dir` built the CastLib shells from the MCsL,
each internal entry got its `lctx` (scripts) connected — which is why
every script in the game worked — but the member map was left empty.
External casts populate via their own preload-result handler; the
movie-internal cast had nothing. CastLib 1 ("内蔵", id 66560, 47
members) stayed an empty shell.

Fix: for non-external MCsL entries whose cast def exists in the
movie's own parsed casts, apply the def (`apply_cast_def_keep`) right
after the shells are built.

### Verified live

- `member(11, 1).type` = `#text`; `the number of member "main"` = 11.
- Sprite 138 renders: `[TEXT_RECT] sprite#138 ... info=844x104`.
- The intro dialogue cycles on click:
  1. "While usually a quiet park with no-one around, it's currently
     bustling families enjoying the Summer."
  2. "I get my, pride and joy, a long ranged camera ready"
  3. "Hiding in my bag the expensive hi-tech video camera ... a girl
     playing at the waterside!!"
  4. "Cautious of my surroundings, I pressed the record button."
  5th click: reset + `go the frame + 1` → 695 → the 248 gate at 696.

Note the raw CASt type ids: 15 = D11.5 rich #text (styled-text XMED
children; dirplayer's `MemberType::Ole` arm handles them), 3 = legacy
field/text, 11 = script, 8 = Flash. The MCsL min/max member windows
per cast lib are in the MCsL dump above.

### Session tooling note

The debug-log probes must wait the full ~60-90s cast preload before
concluding a log line never fires — several earlier probes sampled at
20s and misread "not yet" as "never" (cast_manager/cast_lib lines all
appear late in the load). Also, a `build-vm-dev` output must be
checked for the new debug strings (`strings pkg/vm_rust_bg.wasm`)
before testing — one build this session ran against a stale pkg while
the patch had not landed, costing a full round of false negatives.
