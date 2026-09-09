#!/usr/bin/env python3
"""to_renpy.py - convert the Director 11.5 game "mizube" (RE227368) into a
native Ren'Py project, using only the user's own game files.

Inputs
  --game DIR     directory with mizube.exe, system.cxt, cgoto.cxt, mov*.cct
  --scripts DIR  ProjectorRays decompiled scripts
                 (projectorrays decompile system.cxt --dump-scripts -o DIR)
  --out DIR      output Ren'Py project directory (created)

Output: a Ren'Py 8 project (game/ with script.rpy, options.rpy, gui.rpy,
images/, audio/) that runs the recovered scenario text with the original
artwork and audio. Ren'Py runs natively on Android (RAPT builds an ARM
APK - no emulation involved).

Only stdlib is required; ffmpeg is used opportunistically to transcode
M4A to OGG (Ren'Py does not play AAC).
"""
import argparse
import os
import re
import struct
import subprocess
import sys
import zlib
from collections import defaultdict

# ---------------------------------------------------------------- containers

def read_varint(d, p):
    val = 0
    while True:
        b = d[p]
        p += 1
        val = (val << 7) | (b & 0x7F)
        if not (b & 0x80):
            return val, p


class Rifx:
    """XFIR (little-endian RIFX) container: MV93 and afterburned FGDC."""

    def __init__(self, path):
        self.path = path
        self.data = open(path, 'rb').read()
        d = self.data
        if d[:4] != b'XFIR':
            raise RuntimeError(f'{path}: not an XFIR file')
        self.codec = d[8:12][::-1]
        self.afterburned = self.codec in (b'FGDC', b'FGDM')
        self._ils_buf = b''
        self._ils_chunks = {}
        self.chunks = {}      # id -> (fourCC logical, len, offset info)
        if self.afterburned:
            self._parse_afterburned()
        else:
            self._parse_mv93()

    def _parse_mv93(self):
        d = self.data
        mmap_off = struct.unpack_from('<I', d, 24)[0]
        hdr_len, ent_len = struct.unpack_from('<HH', d, mmap_off + 8)
        cmax, cused = struct.unpack_from('<II', d, mmap_off + 12)
        es = mmap_off + 8 + hdr_len
        for i in range(cmax):
            o = es + i * ent_len
            logical = d[o:o + 4][::-1]
            ln, off = struct.unpack_from('<II', d, o + 4)
            if logical in (b'eerf', b'knuj') or (ln == 0 and off == 0):
                continue
            self.chunks[i] = (logical, ln, off)   # meta = chunk offset

    def _parse_afterburned(self):
        d = self.data
        p = 12
        flen, p = read_varint(d, p + 4)
        p += flen                                   # Fver
        flen, p = read_varint(d, p + 4)             # Fcdr
        p += flen
        alen, p = read_varint(d, p + 4)            # ABMP
        aend = p + alen
        _, p = read_varint(d, p)                   # map compression type
        _, p = read_varint(d, p)                   # map uncompressed length
        ab = zlib.decompress(d[p:aend])
        q = 0
        _, q = read_varint(ab, q)
        _, q = read_varint(ab, q)
        rescount, q = read_varint(ab, q)
        for _ in range(rescount):
            rid, q = read_varint(ab, q)
            off, q = read_varint(ab, q)
            csz, q = read_varint(ab, q)
            usz, q = read_varint(ab, q)
            ct, q = read_varint(ab, q)
            tag = struct.unpack_from('<I', ab, q)[0]
            q += 4
            self.chunks[rid] = (tag.to_bytes(4, 'big'), csz, (off, usz, ct))
        # FGEI + ILS
        p = aend
        _, p = read_varint(d, p + 4)
        ils_off = p
        ils = self.chunks.get(2)
        if ils:
            _, csz, (off, usz, ct) = ils
            self._ils_buf = zlib.decompress(d[ils_off:ils_off + csz])
            r = 0
            while r < len(self._ils_buf):
                rid, r = read_varint(self._ils_buf, r)
                info = self.chunks.get(rid)
                if not info:
                    break
                ln = info[1]
                self._ils_chunks[rid] = (r, ln)
                r += ln
        self._ils_off = ils_off

    def body(self, cid):
        logical, ln, meta, = self.chunks[cid]
        if self.afterburned:
            off, usz, ct = meta
            if off == 0xFFFFFFFF:
                base, length = self._ils_chunks[cid]
                raw = self._ils_buf[base:base + length]
            else:
                raw = self.data[self._ils_off + off:self._ils_off + off + ln]
            if ct == 0 and len(raw) >= 2 and raw[:2] in (b'\x78\xda', b'\x78\x9c'):
                try:
                    return zlib.decompress(raw)
                except zlib.error:
                    return raw
            return raw
        return self.data[meta + 8:meta + 8 + ln]   # meta is the raw offset

    def find(self, fourcc):
        return [cid for cid, (l, _, _) in self.chunks.items() if l == fourcc]


# ---------------------------------------------------------------- cast tables

class Cast:
    def __init__(self, path, name):
        self.name = name
        self.rifx = Rifx(path)
        self.members = {}       # member number -> dict
        self._load()

    def _load(self):
        r = self.rifx
        cas_ids = r.find(b'CAS*')
        if not cas_ids:
            return
        casd = r.body(cas_ids[0])
        slots = [struct.unpack_from('>i', casd, i)[0] for i in range(0, len(casd), 4)]
        # KEY* media table: {u16 es1, u16 es2, u32 cnt, u32 used} +
        # cnt x {i32 sectionID, i32 owner, u32 fourCC}
        media = defaultdict(list)
        key_ids = r.find(b'KEY*')
        if key_ids:
            kd = r.body(key_ids[0])
            cnt = struct.unpack_from('<I', kd, 4)[0]
            for i in range(cnt):
                sid, owner, fcc = struct.unpack_from('<iii', kd, 12 + i * 12)
                if sid == -1:
                    continue
                f = struct.pack('>I', fcc & 0xFFFFFFFF).decode('latin1')
                media[owner].append((sid, f))
        for idx, sec in enumerate(slots):
            if sec <= 0 or sec not in r.chunks or r.chunks[sec][0] != b'CASt':
                continue
            b = r.body(sec)
            if len(b) < 12:
                continue
            typ, ilen, slen = struct.unpack_from('>III', b, 0)
            m = {'number': idx + 1, 'section': sec, 'type': typ,
                 'name': '', 'media': []}
            info = b[12:12 + ilen]
            if len(info) >= 20:
                data_off = struct.unpack_from('>I', info, 0)[0]
                if data_off + 2 <= len(info):
                    tbl = struct.unpack_from('>H', info, data_off)[0]
                    offs = [struct.unpack_from('>I', info, data_off + 2 + 4 * k)[0]
                            for k in range(tbl)]
                    base = data_off + 2 + 4 * tbl + 4
                    if tbl >= 2 and offs[1] < 0x10000 and base + offs[1] < len(info):
                        o2 = base + offs[1]
                        nl = info[o2]
                        m['name'] = info[o2 + 1:o2 + 1 + nl].decode('utf-8', 'replace')
            if typ == 1 and slen >= 10:   # bitmap geometry
                m['height'] = struct.unpack_from('>H', b, 12 + ilen + 6)[0]
                m['width'] = struct.unpack_from('>H', b, 12 + ilen + 8)[0]
            m['media'] = media.get(sec) or media.get(idx + 1) or []
            self.members[idx + 1] = m


# ---------------------------------------------------------------- helpers

def safe_name(s, fallback):
    s = re.sub(r'[^A-Za-z0-9_-]+', '_', s).strip('_')
    return s or fallback


def probe_audio(data):
    if data[:3] == b'ID3':
        return '.mp3'
    if data[:4] == b'RIFF':
        return '.wav'
    if len(data) > 12 and data[4:8] == b'ftyp':
        return '.m4a'
    if len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return '.mp3'
    return None


# ---------------------------------------------------------------- script parse

STN_RE = re.compile(r'stn\(\s*"((?:[^"\\]|\\.)*)"\s*(?:,\s*\d+\s*)?\)')
SOUND_RE = re.compile(r'puppetSound\(\s*\d+\s*,\s*"([^"]+)"\s*\)')


def parse_lingo_scripts(scripts_dir):
    """Extract per-scene dialogue and sound cues from decompiled Lingo.

    The game's CastScripts use the pattern:
        case qq1 of          -- qq1: scene counter
          15:
            case ssina of     -- ssina: click counter (advanced per mouseUp)
              1: stn("line", 1)
              6: go(the frame + 1)
            end case
        end case
    We linearize that into scenes[qq1][ssina] -> list of events.
    """
    scenes = defaultdict(lambda: defaultdict(list))
    misc_lines = []
    sounds = set()
    files = []
    for root, _, names in os.walk(scripts_dir):
        for n in names:
            if n.endswith('.ls'):
                files.append(os.path.join(root, n))
    files.sort(key=lambda p: [int(t) if t.isdigit() else t
                              for t in re.split(r'(\d+)', p)])

    def emit(kind, value, qq1, ssina):
        if qq1 is not None:
            if ssina is None:
                ssina = (max(scenes[qq1]) + 1) if scenes[qq1] else 1
            scenes[qq1][ssina].append((kind, value))
        else:
            misc_lines.append((kind, value))

    for path in files:
        try:
            text = open(path, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        state = 0        # 0 body, 1 in 'case qq1 of', 2 in a qq1 branch, 3 in 'case ssina of'
        qq1 = None
        ssina = None
        for line in text.splitlines():
            ls = line.strip()
            if re.match(r'case\s+qq1\s+of', ls):
                state, qq1, ssina = 1, None, None
                continue
            if re.match(r'case\s+ssina\s+of', ls) and state in (1, 2):
                state, ssina = 3, None
                continue
            if ls.startswith('end case'):
                if state == 3:
                    state, ssina = 2, None
                elif state == 2:
                    state, qq1 = 0, None
                elif state == 1:
                    state = 0
                continue
            m = re.match(r'(\d+)\s*:\s*$', ls)
            if m:
                if state == 1:
                    qq1, state = int(m.group(1)), 2
                elif state == 2:
                    # a second qq1 branch directly (no ssina case)
                    qq1 = int(m.group(1))
                elif state == 3:
                    ssina = int(m.group(1))
                continue
            # content
            for sm in SOUND_RE.finditer(ls):
                sounds.add(sm.group(1))
                emit('sound', sm.group(1), qq1, ssina)
            for sm in STN_RE.finditer(ls):
                emit('stn', sm.group(1), qq1, ssina)
            if re.search(r'go\(the frame\s*\+\s*1\)', ls):
                emit('adv', '', qq1, ssina)
    return scenes, misc_lines, sounds


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True)
    ap.add_argument('--scripts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--max-frames', type=int, default=0,
                    help='limit extracted JPEG frames (0 = all)')
    ap.add_argument('--font', default=None,
                    help='path to a Japanese-capable TTF/OTF font to bundle '
                         '(e.g. Noto Sans JP); required for Japanese text')
    args = ap.parse_args()

    game = os.path.abspath(args.game)
    out = os.path.abspath(args.out)
    game_dir = os.path.join(out, 'game')
    img_dir = os.path.join(game_dir, 'images')
    aud_dir = os.path.join(game_dir, 'audio')
    for p in (img_dir, aud_dir):
        os.makedirs(p, exist_ok=True)

    casts = [
        ('mov', 'mov.cct'), ('mov2', 'mov2.cct'), ('mov3', 'mov3.cct'),
        ('mov4', 'mov4.cct'), ('mov5', 'mov5.cct'), ('mov6', 'mov6.cct'),
        ('mov7', 'mov7.cct'), ('mov8', 'mov8.cct'), ('cgoto', 'cgoto.cxt'),
    ]

    # ---- images: JPEG frames from the mov casts
    n_img = 0
    anim_groups = defaultdict(list)    # cast -> [(name, file)]
    for cast_name, fname in casts[:8]:
        c = Cast(os.path.join(game, fname), cast_name)
        used = defaultdict(int)
        for num in sorted(c.members):
            m = c.members[num]
            if m['type'] != 1:
                continue
            medi = [cid for cid, f in m['media'] if f == 'ediM']
            data = None
            for cid in medi:
                try:
                    b = c.rifx.body(cid)
                except Exception:
                    continue
                if b[:3] == b'\xff\xd8\xff':
                    data = b
                    break
            if data is None:
                continue
            base = safe_name(m['name'], f'member{num:04d}')
            used[base] += 1
            fn = base if used[base] == 1 else f'{base}_{used[base]}'
            rel = os.path.join(img_dir, cast_name, fn + '.jpg')
            os.makedirs(os.path.dirname(rel), exist_ok=True)
            with open(rel, 'wb') as f:
                f.write(data)
            anim_groups[cast_name].append((fn, f'images/{cast_name}/{fn}.jpg'))
            n_img += 1
            if args.max_frames and n_img >= args.max_frames:
                break
        if args.max_frames and n_img >= args.max_frames:
            break
    print(f'[to_renpy] extracted {n_img} JPEG frames')

    # ---- audio: named MP3/M4A members from cgoto
    c = Cast(os.path.join(game, 'cgoto.cxt'), 'cgoto')
    sound_files = {}     # member name -> relative path
    n_aud = 0
    for num in sorted(c.members):
        m = c.members[num]
        if m['type'] != 6 or not m['name']:
            continue
        data = None
        ext = None
        for cid, f in m['media']:
            if f != 'ediM':
                continue
            try:
                b = c.rifx.body(cid)
            except Exception:
                continue
            e = probe_audio(b)
            if e:
                data, ext = b, e
                break
        if data is None:
            continue
        base = safe_name(m['name'], f'sound{num:04d}')
        rel = f'audio/{base}{ext}'
        with open(os.path.join(game_dir, rel), 'wb') as f:
            f.write(data)
        if ext == '.m4a':
            # Ren'Py does not play AAC - transcode to OGG when ffmpeg exists
            ogg = os.path.join(game_dir, f'audio/{base}.ogg')
            try:
                subprocess.run(['ffmpeg', '-y', '-loglevel', 'error',
                                '-i', os.path.join(game_dir, rel),
                                '-c:a', 'libvorbis', ogg], timeout=120, check=True)
                rel = f'audio/{base}.ogg'
            except Exception:
                print(f'[to_renpy] WARNING: could not transcode {base}.m4a '
                      f'(install ffmpeg); sound will not play')
        sound_files[m['name']] = rel
        n_aud += 1
    print(f'[to_renpy] extracted {n_aud} named audio members')

    # ---- story from decompiled scripts
    scenes, misc, cue_sounds = parse_lingo_scripts(args.scripts)
    total_lines = sum(len(v) for s in scenes.values() for v in s.values())
    total_lines += len(misc)
    print(f'[to_renpy] story: {len(scenes)} scenes, {total_lines} dialogue lines, '
          f'{len(cue_sounds)} distinct sound cues')

    # ---- fonts
    font_rel = None
    if args.font:
        os.makedirs(os.path.join(game_dir, 'fonts'), exist_ok=True)
        import shutil
        shutil.copy(args.font, os.path.join(game_dir, 'fonts', 'main.ttf'))
        font_rel = 'fonts/main.ttf'
        print(f'[to_renpy] bundled font: {args.font}')
    else:
        print('[to_renpy] WARNING: no --font given; Japanese text will not '
              'render with the default font')

    # ---- generate Ren'Py files
    with open(os.path.join(game_dir, 'options.rpy'), 'w', encoding='utf-8') as f:
        f.write(OPTIONS_RPY)
    with open(os.path.join(game_dir, 'gui.rpy'), 'w', encoding='utf-8') as f:
        f.write(GUI_RPY if font_rel else '')
    gen_animations(game_dir, anim_groups)
    gen_story(game_dir, scenes, misc, sound_files, img_dir, anim_groups)
    print(f'[to_renpy] project written to {out}')


def gen_animations(game_dir, anim_groups):
    """Frame sequences -> ATL animations (grouped by numeric suffix runs)."""
    lines = ['# Automatic: animation definitions from original frame members', '']
    for cast, items in anim_groups.items():
        # group by prefix before the trailing number
        groups = defaultdict(list)
        for fn, rel in items:
            m = re.match(r'^(.*?)_?(\d+)$', fn)
            key = m.group(1) if m else fn
            groups[key].append(rel)
        for key, rels in groups.items():
            if len(rels) < 2:
                continue
            name = f'anim_{cast}_{safe_name(key, "seq")}'
            lines.append(f'image {name}:')
            lines.append('    block:')
            for rel in sorted(rels):
                lines.append(f'        "{rel}"')
                lines.append('        0.1')
            lines.append('    repeat')
            lines.append('')
    with open(os.path.join(game_dir, 'animations.rpy'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def gen_story(game_dir, scenes, misc, sound_files, img_dir, anim_groups):
    # pick a background: first extracted frame
    bg = None
    for cast, items in anim_groups.items():
        if items:
            bg = sorted(items, key=lambda t: t[1])[0][1]
            break
    out = []
    w = out.append
    w('# Automatic conversion of the "mizube" scenario (Lingo -> Ren\'Py).')
    w('# Dialogue lines are the original stn() strings, grouped by the')
    w('# original scene counter (qq1) and click step (ssina).')
    w('')
    w('define n = Character(None)')
    w('')
    w('label start:')
    if bg:
        w('    scene black')
        w(f'    show expression "{bg}" as bg')
    w('    "水辺 (mizube) - native Ren\'Py conversion (proof of concept)"')
    w('    "The scenario below is the recovered original dialogue, linearized."')
    w('    jump story_flow')
    w('')
    for qq1 in sorted(scenes):
        w(f'label scene_{qq1:03d}:')
        steps = scenes[qq1]
        for ssina in sorted(steps):
            for kind, txt in steps[ssina]:
                if kind == 'stn':
                    t = txt.replace('\\', '\\\\').replace('"', '\\"')
                    w(f'    n "{t}"')
                elif kind == 'sound':
                    rel = sound_files.get(txt)
                    if rel:
                        w(f'    play sound "{rel}"')
        w('')
    if misc:
        w('label misc_dialogue:')
        for kind, txt in misc:
            if kind == 'stn':
                t = txt.replace('\\', '\\\\').replace('"', '\\"')
                w(f'    n "{t}"')
        w('')
    # linear flow: visit scenes in qq1 order
    w('label story_flow:')
    for qq1 in sorted(scenes):
        w(f'    call scene_{qq1:03d}')
    if misc:
        w('    call misc_dialogue')
    w('    "— end of converted scenario —"')
    w('    return')
    with open(os.path.join(game_dir, 'script.rpy'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')


OPTIONS_RPY = '''\
# Automatic: project options
define config.name = "mizube (native Ren'Py conversion)"
define config.version = "0.1"
define config.screen_width = 960
define config.screen_height = 720
define config.save_directory = "mizube-renpy"

init python:
    gui.text_font = "fonts/main.ttf"
    gui.interface_text_font = "fonts/main.ttf"
    gui.name_text_font = "fonts/main.ttf"
    gui.default_font = "fonts/main.ttf"
'''

GUI_RPY = '''\
# Automatic: minimal GUI overrides (Japanese-capable font)
define gui.text_font = "fonts/main.ttf"
define gui.interface_text_font = "fonts/main.ttf"
define gui.name_text_font = "fonts/main.ttf"
define gui.default_font = "fonts/main.ttf"
'''


if __name__ == '__main__':
    sys.exit(main())
