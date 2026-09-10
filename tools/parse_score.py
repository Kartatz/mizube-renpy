#!/usr/bin/env python3
"""parse_score.py - Director 11.5 score parser for mizube (RE227368).

The single missing piece of the port: the Director score tells us every
sprite's channel, cast member, position, size, ink/blend, and timing, for
every frame of the game, plus the marker (go() target) table.

Sources:
  - the embedded main movie inside mizube.exe (extracted by extract_movie.py
    to an XFIR/MV93 file) holds VWSC (score), VWLB (labels), MCsL (cast list),
    Lnam (string pool), and its own internal cast
  - the external casts (system.cxt cgoto.cxt mov*.cct) hold the member names

VWSC layout (D6+ family, verified against ScummVM engines/director/score.cpp
adapted for the D11.5 framesVersion=14 / 48-byte sprite records):
  u32 framesStreamSize, i32 ver=-3, u32 listStart
  @listStart: i32 numEntries, i32 listSize, i32 maxDataLen
  u32 offsets[numEntries]        (relative to frameDataOffset)
  frameDataOffset = listStart+12 + listSize*4:
    u32 framesStreamSize, u32 frame1Offset, u32 numOfFrames,
    u16 framesVersion, u16 spriteRecordSize, u16 numChannels,
    u16 numChannelsDisplayed
    then frame records:  u16 frameSize, then patches
    { u16 channelSize, u16 channelOffset, bytes[channelSize] } ...
  Channel data space: 288 bytes of main channels (script@0, tempo@48,
  transition@96, sound2@144, sound1@192, palette@240), then 48-byte sprite
  records for sprite channel p at 288+48*p (Director channel p+1).
  Frames are delta-compressed: patches apply onto the previous frame.

  Sprite record (48 bytes, BE): type u8, ink u8, fore u8, back u8,
  castLib i16, member u16, spriteListIdx u32, y i16, x i16, h i16, w i16,
  colorcode u8, blend u8, thickness u8, flags u8, fgG/bgG/fgB/bgB u8 x4,
  angleRot u32, angleSkew u32, pad x12.

  Sprite-detail offset array (offsets[], triplet per sprite):
    entry[i]   = SpriteInfo {startFrame,endFrame,xtraInfo,flags,channelNum,
                TweenInfo(5 x i32), keyFrames[] i32}
    entry[i+1] = BehaviorElement[] {castLib i16, member i16, initIdx i32}
    entry[i+2] = sprite name (NUL-terminated)

VWLB layout (D11.5, verified):
  u16 entryCount, u16 ver=11, entries {u16 strOff, u16 frame}[entryCount]
  (last entry is a terminator), string blob at entryCount*4+2; label i =
  blob[strOff[i]:strOff[i+1]].

Outputs (--out DIR):
  markers.json, score_frames.json, score.txt
"""
import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from to_renpy import Rifx, Cast          # noqa: E402

MAIN_CH_SIZE = 288
SPR_CH_SIZE = 48
MAIN_OFF = {'script': 0, 'tempo': 48, 'transition': 96, 'sound2': 144,
            'sound1': 192, 'palette': 240}
INK_NAMES = {0: 'copy', 1: 'transparent', 8: 'reverse', 16: 'ghost',
             32: 'noBackground', 33: 'noBackground2', 34: 'matte',
             36: 'lighten', 37: 'darken', 38: 'add', 39: 'addpin',
             40: 'subtract', 41: 'subpin', 42: 'darkest', 50: 'blend',
             51: 'blendDither', 52: 'addDither'}


def u16(d, p):
    return struct.unpack_from('>H', d, p)[0]


def i16(d, p):
    return struct.unpack_from('>h', d, p)[0]


def u32(d, p):
    return struct.unpack_from('>I', d, p)[0]


def i32(d, p):
    return struct.unpack_from('>i', d, p)[0]


# ---------------------------------------------------------------- labels

def parse_vwlb(b):
    count, ver = struct.unpack_from('>HH', b, 0)
    entries = [struct.unpack_from('>HH', b, 4 + 4 * i) for i in range(count)]
    base = count * 4 + 6          # entries end at 4+4*count; 2 pad bytes
    labels = []
    for i in range(count - 1):          # last entry is the terminator
        s0, frame = entries[i]
        s1 = entries[i + 1][0]
        name = b[base + s0:base + s1].decode('latin1')
        labels.append((frame, name))
    return labels


# ---------------------------------------------------------------- score

class Score:
    def __init__(self, vWSC):
        b = self.b = vWSC
        size, ver, list_start = struct.unpack_from('>IiI', b, 0)
        assert ver == -3, f'unexpected VWSC version {ver}'
        self.num_entries, self.list_size, self.max_data_len = \
            struct.unpack_from('>iii', b, list_start)
        index_start = list_start + 12
        self.frame_data_off = index_start + self.list_size * 4
        self.offsets = struct.unpack_from(
            '>%dI' % self.num_entries, b, index_start)

        self.frames_size, self.frame1_off, self.num_frames, \
            self.frames_version, self.sprite_rec_size, self.num_channels = \
            struct.unpack_from('>IIIHHH', b, self.frame_data_off)
        if self.frames_version > 13:
            self.num_channels_disp = u16(b, self.frame_data_off + 18)
            self.first_frame_pos = self.frame_data_off + 20
        else:
            self.num_channels_disp = 120 if self.frames_version > 7 else 48
            self.first_frame_pos = self.frame_data_off + 20
        assert self.sprite_rec_size == 48, self.sprite_rec_size

    def detail(self, idx):
        """sprite-detail entry data (SpriteInfo / Behavior / Name triplets)"""
        if idx <= 0 or idx >= self.num_entries:
            return b''
        off = self.offsets[idx]
        end = self.offsets[idx + 1] if idx + 1 < self.num_entries \
            else self.max_data_len
        if end < off:
            return b''
        return self.b[self.frame_data_off + off:self.frame_data_off + end]

    def parse_sprite_info(self, idx):
        d = self.detail(idx)
        if len(d) < 24:
            return None
        info = {
            'startFrame': i32(d, 0), 'endFrame': i32(d, 4),
            'xtraInfo': i32(d, 8), 'flags': u32(d, 12),
            'channelNum': i32(d, 16),
            'tween': struct.unpack_from('>iiiii', d, 20),
            'keyFrames': [i32(d, p) for p in range(40, len(d), 4)],
        }
        return info

    def parse_behaviors(self, idx):
        d = self.detail(idx)
        out = []
        p = 0
        while p + 8 <= len(d):
            cast_lib, member = struct.unpack_from('>hh', d, p)
            init_idx = i32(d, p + 4)
            params = None
            if init_idx:
                pd = self.detail(init_idx)
                if pd:
                    params = pd.split(b'\x00')[0].decode('latin1', 'replace')
            out.append({'castLib': cast_lib, 'member': member,
                        'params': params})
            p += 8
        return out

    def parse_name(self, idx):
        d = self.detail(idx)
        if not d:
            return None
        return d.split(b'\x00')[0].decode('latin1', 'replace')

    def sprite_details(self, sprite_list_idx):
        """{info, behaviors, name} for a sprite's detail triplet"""
        if not sprite_list_idx:
            return None
        return {
            'info': self.parse_sprite_info(sprite_list_idx),
            'behaviors': self.parse_behaviors(sprite_list_idx + 1),
            'name': self.parse_name(sprite_list_idx + 2),
        }

    def frames(self):
        """Yield per-frame dicts (delta-decoded)."""
        buf = bytearray(MAIN_CH_SIZE + SPR_CH_SIZE * self.num_channels)
        p = self.first_frame_pos
        end = self.frame_data_off + self.frames_size
        frame_no = 0
        while p < end - 2:
            frame_no += 1
            frame_size = u16(self.b, p)
            p += 2
            if frame_size == 0:
                break
            remaining = frame_size - 2
            while remaining > 0:
                ch_size, ch_off = struct.unpack_from('>HH', self.b, p)
                p += 4
                buf[ch_off:ch_off + ch_size] = self.b[p:p + ch_size]
                p += ch_size
                remaining -= ch_size + 4
            yield frame_no, bytes(buf)

    def decode_main(self, buf):
        m = {}
        m['script'] = {'castLib': i16(buf, 0), 'member': u16(buf, 2),
                       'idx': u32(buf, 4)}
        m['tempo'] = {'idx': u32(buf, 48), 'cue': u16(buf, 52),
                      'tempo': buf[54]}
        m['transition'] = {'castLib': i16(buf, 96), 'member': u16(buf, 98),
                           'idx': u32(buf, 100)}
        m['sound2'] = {'castLib': i16(buf, 144), 'member': u16(buf, 146),
                       'idx': u32(buf, 148)}
        m['sound1'] = {'castLib': i16(buf, 192), 'member': u16(buf, 194),
                       'idx': u32(buf, 196)}
        m['palette'] = {'castLib': i16(buf, 240), 'member': i16(buf, 242)}
        return m

    def main_behaviors(self, main_ch):
        """behaviors wired to the main channels (script/tempo/etc.)"""
        out = {}
        for k in ('script', 'tempo', 'transition', 'sound1', 'sound2'):
            idx = main_ch[k].get('idx')
            out[k] = self.parse_behaviors(idx + 1) if idx else []
        return out

    def decode_sprites(self, buf):
        out = []
        for slot in range(self.num_channels):
            o = MAIN_CH_SIZE + SPR_CH_SIZE * slot
            member = u16(buf, o + 6)
            w, h = i16(buf, o + 18), i16(buf, o + 16)
            if member == 0 or w <= 0 or h <= 0:
                continue
            ink = buf[o + 1] & 0x3f
            out.append({
                'channel': slot + 1,
                'type': buf[o], 'ink': INK_NAMES.get(ink, ink),
                'blend': buf[o + 21],
                'castLib': i16(buf, o + 4), 'member': member,
                'x': i16(buf, o + 14), 'y': i16(buf, o + 12),
                'w': w, 'h': h,
                'colorcode': buf[o + 20],
                'moveable': bool(buf[o + 20] & 0x80),
                'editable': bool(buf[o + 20] & 0x40),
                'angle': u32(buf, o + 28),
                'idx': u32(buf, o + 8),
            })
        return out


# ---------------------------------------------------------------- cast libs

class CastResolver:
    """castLib number -> {member: name} using MCsL order + the .cct files."""

    def __init__(self, movie_rifx, game_dir):
        self.libs = {}               # lib index -> name or None (internal)
        self.names = {}              # lib index -> {member: name}
        self.types = {}              # lib index -> {member: type}
        m = movie_rifx.body(movie_rifx.find(b'MCsL')[0])
        data_off = struct.unpack_from('>I', m, 0)[0]
        tbl = struct.unpack_from('>H', m, data_off)[0]
        offs = [struct.unpack_from('>I', m, data_off + 2 + 4 * k)[0]
                for k in range(tbl)]
        base = data_off + 2 + 4 * tbl + 4

        def item(k):
            if k >= tbl or offs[k] == 0:
                return ''
            p = base + offs[k]
            n = m[p]
            return m[p + 1:p + 1 + n].decode('utf-8', 'replace')

        # group of 4 per cast, starting with the internal cast at 0.
        # Verified against the score: sprite castLib N (N>=1) -> MCsL cast
        # N-1, i.e. lib1=internal, lib2=system, lib3=cgoto, lib4=mov,
        # lib5=mov2, lib6=mov5, lib7=mov6, lib8=mov7, lib9=mov8,
        # lib10=mov3, lib11=mov4 (2625/2689 exact geometry matches).
        order = []
        for k in range(tbl // 4):
            name = item(4 * k + 1)
            order.append(name or '*internal')
        self.order = order
        self._movie = movie_rifx
        self._game_dir = game_dir
        self._casts = {}

    def _cast_for(self, lib):
        idx = lib - 1 if lib >= 1 else 0
        if idx < 0 or idx >= len(self.order):
            return (None, None)
        name = self.order[idx]
        if name == '*internal':
            return ('*internal', self._movie)
        path = None
        for cand in (name + '.cct', name + '.cxt'):
            f = os.path.join(self._game_dir, cand)
            if os.path.exists(f):
                path = f
                break
        if not path:
            return (name, None)
        if name not in self._casts:
            self._casts[name] = Cast(path, name)
        return (name, self._casts[name])

    def member_info(self, lib, member):
        # mov2 (lib5) member numbers are one lower than our Cast numbering
        # (its CAS* carries a phantom leading slot); verified by unique
        # geometry anchors: grandpa 83x212 @ #12 = Cast#11, ore0 312x404
        # @ #26 = Cast#25, a10_00000 960x720 @ #929 = Cast#928.
        if lib == 5:
            member = member - 1
        if lib not in self.names:
            name, cast = self._cast_for(lib)
            if cast is None:
                self.names[lib], self.types[lib] = {}, {}
            elif name == '*internal':
                # parse the movie's own CASt members
                names, types = {}, {}
                try:
                    r = cast
                    casd = r.body(r.find(b'CAS*')[0])
                    slots = [struct.unpack_from('>i', casd, i)[0]
                             for i in range(0, len(casd), 4)]
                    for idx, sec in enumerate(slots):
                        if sec <= 0 or sec not in r.chunks or \
                                r.chunks[sec][0] != b'CASt':
                            continue
                        b = r.body(sec)
                        if len(b) < 12:
                            continue
                        typ, ilen, _ = struct.unpack_from('>III', b, 0)
                        info = b[12:12 + ilen]
                        nm = ''
                        if len(info) >= 20:
                            doff = struct.unpack_from('>I', info, 0)[0]
                            if doff + 2 <= len(info):
                                t2 = struct.unpack_from('>H', info, doff)[0]
                                if t2 >= 2:
                                    o2 = doff + 2 + 4 * t2 + 4 + \
                                        struct.unpack_from(
                                            '>I', info, doff + 2 + 4)[0]
                                    if o2 < len(info):
                                        nl = info[o2]
                                        nm = info[o2 + 1:o2 + 1 + nl].decode(
                                            'utf-8', 'replace')
                        names[idx + 1] = nm
                        types[idx + 1] = typ
                except Exception:
                    pass
                self.names[lib], self.types[lib] = names, types
            else:
                names = {n: m.get('name', '')
                         for n, m in cast.members.items()}
                types = {n: m.get('type', 0)
                         for n, m in cast.members.items()}
                self.names[lib], self.types[lib] = names, types
        nm = self.names[lib].get(member, '')
        tp = self.types[lib].get(member, 0)
        return nm, tp


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--movie', required=True,
                    help='extracted movie (from extract_movie.py)')
    ap.add_argument('--game', required=True,
                    help='original game dir (mizube.exe, *.cct, *.cxt)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--max-frames', type=int, default=0,
                    help='stop after N frames (0 = all)')
    ap.add_argument('--behaviors', action='store_true',
                    help='include sprite behaviors/scripts in dumps')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    r = Rifx(args.movie)
    score = Score(r.body(r.find(b'VWSC')[0]))
    print(f'VWSC: {score.num_frames} frames declared, {score.num_channels} '
          f'channels ({score.num_channels_disp} displayed), '
          f'frames region {score.frames_size} B, '
          f'{score.num_entries} sprite-detail entries')

    labels = parse_vwlb(r.body(r.find(b'VWLB')[0]))
    by_frame = {}
    for frame, name in labels:
        by_frame.setdefault(frame, []).append(name)
    print(f'VWLB: {len(labels)} markers, frames '
          f'{min(f for f, _ in labels)}..{max(f for f, _ in labels)}')

    resolver = CastResolver(r, args.game)
    print('cast libs (MCsL order):', resolver.order)

    frames_out = []
    txt = open(os.path.join(args.out, 'score.txt'), 'w')
    for frame_no, buf in score.frames():
        main_ch = score.decode_main(buf)
        sprites = score.decode_sprites(buf)
        names_here = by_frame.get(frame_no, [])
        rec = {'frame': frame_no, 'markers': names_here, 'main': main_ch,
               'sprites': sprites}
        if args.max_frames and frame_no > args.max_frames:
            break
        if args.behaviors:
            rec['mainBehaviors'] = score.main_behaviors(main_ch)

        txt.write(f'===== FRAME {frame_no} '
                  f'({", ".join(names_here) if names_here else "-"}) =====\n')
        tempo = main_ch['tempo']['tempo']
        s1 = main_ch['sound1']
        s2 = main_ch['sound2']
        sc = main_ch['script']
        tr = main_ch['transition']
        bits = []
        if tempo:
            bits.append(f'tempo={tempo}')
        if s1['member']:
            bits.append(f'snd1={s1["castLib"]}:{s1["member"]}')
        if s2['member']:
            bits.append(f'snd2={s2["castLib"]}:{s2["member"]}')
        if sc['member']:
            n, _ = resolver.member_info(sc['castLib'], sc['member'])
            bits.append(f'script={sc["castLib"]}:{sc["member"]}({n})')
        if tr['member']:
            bits.append(f'trans={tr["castLib"]}:{tr["member"]}')
        if bits:
            txt.write('  MAIN: ' + ' '.join(bits) + '\n')
        for s in sprites:
            nm, tp = resolver.member_info(s['castLib'], s['member'])
            s['name'] = nm
            s['memberType'] = tp
            if args.behaviors and s['idx']:
                s['details'] = score.sprite_details(s['idx'])
            txt.write('  ch%-3d %-28s lib%d:#%-4d (%3d,%3d) %3dx%3d '
                      'ink=%-12s blend=%3d%s\n' % (
                          s['channel'], (nm or '?')[:28], s['castLib'],
                          s['member'], s['x'], s['y'], s['w'], s['h'],
                          s['ink'], s['blend'],
                          ' [MOVE]' if s['moveable'] else ''))
        frames_out.append(rec)

    txt.close()
    with open(os.path.join(args.out, 'markers.json'), 'w') as f:
        json.dump({'labels': [{'frame': fr, 'name': n} for fr, n in labels],
                   'order': resolver.order}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(args.out, 'score_frames.json'), 'w') as f:
        json.dump({'castOrder': resolver.order, 'frames': frames_out},
                  f, ensure_ascii=False)
    print(f'parsed {len(frames_out)} frames -> {args.out}/score_frames.json,'
          f' score.txt, markers.json')


if __name__ == '__main__':
    main()
