#!/usr/bin/env python3
"""extract_movie.py - pull the embedded main movie out of the mizube.exe
projector, rebase its EXE-absolute mmap offsets, and write a standalone
XFIR/MV93 file the standard Rifx parser can walk.

Verified projector layout:
  0x58000 : "10JP" file table (5 x 52-byte entries: proj/dirapi/iml32 dlls)
  0x448158: APPL archive (XFIR LE, Xtra DLLs, Dict chunk)
  0x86c8c8: embedded main movie, XFIR(MV93), ~2.78 MB

XFIR/MV93 file layout (same as the game's .cct/.cxt casts):
  +0  'XFIR'  u32 size  '39VM' (MV93 codec, reversed)
  +12 'pami' (imap) chunk: u32 len=0x18, body = {u32 id, u32 mmapOff, ...}
  +24 (file offset) = imap body field 2 = mmap chunk offset
  mmap entries: 20 bytes {fourCC-reversed, u32 len, u32 off, u32 a, u32 b}
  starting at mmap + 32 (8 tag/len + hdr_len 24); hdr: u16 hdrLen,u16 entLen,
  u32 cmax, u32 cused at mmap+8.

The embedded movie's mmap chunk offsets are EXE-absolute; every offset
>= movie base is rebased by subtracting the base. Offsets that fall below
the movie base reference the APPL region and are flagged.
"""
import struct
import sys

MOVIE_BASE = 0x86c8c8

def main(exe_path, out_path):
    d = open(exe_path, 'rb').read()
    base = MOVIE_BASE
    if d[base:base + 4] != b'XFIR':
        print('no XFIR at 0x%x, got %r' % (base, d[base:base + 4]))
        return 1
    size = struct.unpack_from('<I', d, base + 4)[0]
    codec = d[base + 8:base + 12]
    print('XFIR size=%d codec=%r' % (size, codec))

    rel_mmap_off = struct.unpack_from('<I', d, base + 24)[0]
    mmap_abs = base + rel_mmap_off
    # EXE-absolute pointer stored in imap? (points inside the movie region
    # when interpreted raw). Distinguish by checking the tag at that spot.
    raw = struct.unpack_from('<I', d, base + 24)[0]
    if raw >= base and d[raw:raw + 4] == b'pamm':
        mmap_off = raw - base          # EXE-absolute pointer, rebase
        print('imap mmap ptr EXE-absolute 0x%x -> %d' % (raw, mmap_off))
    else:
        mmap_off = rel_mmap_off
        print('imap mmap ptr relative: %d' % mmap_off)
    assert d[base + mmap_off:base + mmap_off + 4] == b'pamm', 'mmap tag missing'

    hdr_len, ent_len = struct.unpack_from('<HH', d, base + mmap_off + 8)
    cmax, cused = struct.unpack_from('<II', d, base + mmap_off + 12)
    es = mmap_off + 8 + hdr_len
    print('mmap@%d hdr_len=%d ent_len=%d cmax=%d cused=%d entries@%d' % (
        mmap_off, hdr_len, ent_len, cmax, cused, es))

    entries = []
    below = 0
    for i in range(cmax):
        o = base + es + i * ent_len
        tag = d[o:o + 4]
        ln, off = struct.unpack_from('<II', d, o + 4)
        if tag in (b'eerf', b'knuj') or (ln == 0 and off == 0):
            continue
        entries.append((i, tag, ln, off))
        if off and off < base:
            below += 1
    tags = {}
    for i, tag, ln, off in entries:
        tags.setdefault(tag[::-1], []).append((i, ln, off))
    print('live entries: %d (%d below movie base)' % (len(entries), below))
    for t, lst in sorted(tags.items()):
        print('  %-6s x%-4d tot=%9d  ids=%s' % (
            t.decode('latin1'), len(lst), sum(l for _, l, _ in lst),
            [i for i, _, _ in lst][:10]))
    # offset range
    offs = [off for _, _, _, off in entries if off]
    print('offset range: 0x%x - 0x%x (movie base 0x%x, end 0x%x)' % (
        min(offs), max(offs), base, base + size))

    out = bytearray(d[base:base + 8 + size])
    # rebase imap mmap pointer
    if struct.unpack_from('<I', out, 24)[0] >= base:
        struct.pack_into('<I', out, 24, struct.unpack_from('<I', out, 24)[0] - base)
    # rebase entry offsets
    fixed = 0
    for i, tag, ln, off in entries:
        if off >= base:
            o = es + i * ent_len
            struct.pack_into('<II', out, o + 4, ln, off - base)
            fixed += 1
        elif off:
            print('  chunk %d %r keeps EXE-abs off 0x%x (outside movie!)' % (i, tag, off))
    open(out_path, 'wb').write(bytes(out))
    print('wrote %s: %d bytes, %d offsets rebased by -0x%x' % (
        out_path, len(out), fixed, base))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
