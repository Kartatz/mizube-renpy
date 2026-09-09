#!/usr/bin/env python3
"""extract_overlays.py - decode Director BITD+ALFA sprite pairs into PNGs.

BITD: PackBits-compressed, 32bpp BGRA, bottom-up rows.
ALFA: PackBits-compressed 8-bit alpha mask (some files store a per-row
      count byte: len == w*h + h -> rows are [count, w bytes]).

Outputs transparent PNGs into game/images/overlays/ for the recovered
overlay sprites: the interactive-mode icons (key/rope/aphrodisiac/hand),
protagonist body-part sprites, NPC sprites, and the heroine expression
cycles.
"""
import os
import struct
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PIL import Image

GAME = '/home/runner/game/RE227368'
OUT = 'game/images/overlays'


def packbits(src):
    out = bytearray()
    i = 0
    while i < len(src):
        n = src[i]; i += 1
        if n < 0x80:
            cnt = n + 1
            out += src[i:i+cnt]; i += cnt
        elif n > 0x80:
            cnt = 0x101 - n
            if i < len(src):
                out += bytes([src[i]]) * cnt; i += 1
    return bytes(out)


sys.path.insert(0, '/home/runner/game/mizube-port/tools')
from to_renpy import Cast as DirCast


def _alpha_of(cast, meds, w, h):
    if 'ALFA' not in meds:
        return None
    araw = packbits(cast.body(meds['ALFA']))
    if len(araw) == w * h + h:           # per-row [count, data]
        alpha = bytearray()
        for r in range(h):
            alpha += araw[r*(w+1)+1:(r+1)*(w+1)]
        return bytes(alpha)
    if len(araw) == w * h:
        return araw
    return None


def decode_sprite(cast, meds, w, h):
    # prefer BITD pixels; fall back to the ediM JPEG with ALFA alpha
    if 'BITD' in meds:
        raw = packbits(cast.body(meds['BITD']))
        if len(raw) != w * h * 4:
            raw = None
    else:
        raw = None
    if raw is None:
        if 'ediM' not in meds:
            return None
        import io
        from PIL import Image as PImage
        jpg = PImage.open(io.BytesIO(cast.body(meds['ediM']))).convert('RGBA')
        if jpg.size != (w, h):
            return None
        alpha = _alpha_of(cast, meds, w, h)
        if alpha is None:
            return None
        img = jpg
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, _ = px[x, y]
                px[x, y] = (r, g, b, alpha[y * w + x])
        return img
    alpha = _alpha_of(cast, meds, w, h)
    img = Image.new('RGBA', (w, h))
    px = img.load()
    for y in range(h):
        sy = h - 1 - y                    # bottom-up
        for x in range(w):
            i = (sy * w + x) * 4
            b, g, r, a = raw[i], raw[i+1], raw[i+2], raw[i+3]
            if alpha is not None:
                a = alpha[sy * w + x]
            px[x, y] = (r, g, b, a)
    return img


def safe(name, fallback):
    out = ''.join(ch if (ch.isascii() and (ch.isalnum() or ch in '-_')) else '_'
                  for ch in name)
    out = out.strip('_') or fallback
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    sources = [('system.cxt', 'system')] + [(f'mov{i}.cct', f'mov{i}')
                for i in ['', '2', '3', '4', '5', '6', '7', '8']]
    count = 0
    for fname, tag in sources:
        path = os.path.join(GAME, fname)
        if not os.path.exists(path):
            continue
        cast = DirCast(path, tag)
        for num in sorted(cast.members):
            m = cast.members[num]
            if m['type'] != 1:
                continue
            w, h = m.get('width', 0), m.get('height', 0)
            if not w or not h or w > 420 or h > 470:
                continue
            meds = {f: sid for sid, f in m['media'] if f in ('BITD', 'ALFA', 'ediM') and sid in cast.rifx.chunks}
            if 'BITD' not in meds and 'ediM' not in meds:
                continue
            img = decode_sprite(cast.rifx, meds, w, h)
            if not img:
                continue
            fn = safe(m['name'], f'member{num:04d}')
            out = os.path.join(OUT, f'{tag}_{fn}.png')
            k = 2
            while os.path.exists(out):
                out = os.path.join(OUT, f'{tag}_{fn}_{k}.png')
                k += 1
            img.save(out)
            count += 1
    print(f'[overlays] extracted {count} sprites to {OUT}')


if __name__ == '__main__':
    main()
