#!/usr/bin/env python3
"""dedupe_scenes.py - remove cross-scene duplicate dialogue within day chapters.

The original Lingo sources attach the same conversation handler to multiple
frames (e.g. CastScript 1769 carries the father's dinner dialogue at BOTH
qq1=15 and qq1=18 - a "click the father directly" variant of the advance
handler). The linearized conversion would play such conversations twice in
a row. This pass drops a say-line whose (speaker, text) already appeared
earlier in the same day chapter, unless it is an immediate consecutive
repeat (intentional pacing) or a whitespace/ellipsis beat.
"""
import re
import sys

SAY_RE = re.compile(r'^(    )([A-Za-z_][A-Za-z0-9_]* )?"((?:[^"\\]|\\.)*)"$')
OTHER_RE = re.compile(r'^(    )(?!n |[a-z_]+ )(\S.*)$')

DAYS = {
    'day1': ['scene_010', 'scene_015', 'scene_018'],
    'day2': ['scene_020', 'scene_021', 'scene_025', 'scene_027',
             'scene_030', 'scene_034'],
    'day3': ['scene_037', 'scene_039', 'scene_040', 'scene_042'],
    'day4': ['scene_050', 'scene_051', 'scene_052', 'scene_054',
             'scene_055', 'scene_060'],
}

BEAT_RE = re.compile(r'^[\s\u3000.‥……・…]+$')
# handler copies differ by stray particles/whitespace; compare with those removed
FUZZ_STRIP = re.compile(r'[\s\u3000をはがにとはですます、。！？]')


def is_beat(text):
    return bool(BEAT_RE.match(text))


def fuzzy_key(speaker, text):
    return speaker + '|' + FUZZ_STRIP.sub('', text)


def dedupe_label(text, seen):
    """Drop repeated non-beat say lines; keep everything else."""
    out = []
    prev_say = None
    for line in text.split('\n'):
        m = SAY_RE.match(line)
        if m and not line.lstrip().startswith('#'):
            speaker = (m.group(2) or 'n ').strip()
            text_jp = m.group(3)
            key = fuzzy_key(speaker, text_jp)
            if (not is_beat(text_jp)
                    and key in seen
                    and prev_say != key):
                continue    # duplicate from a stale handler copy - drop
            if not is_beat(text_jp):
                seen.add(key)
            prev_say = key
            out.append(line)
            continue
        prev_say = None
        out.append(line)
    return '\n'.join(out)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'game/script.rpy'
    src = open(path, encoding='utf-8').read()

    # split into label blocks
    parts = re.split(r'(^label .*$)', src, flags=re.M)
    labels = {}
    order = []
    for i in range(1, len(parts), 2):
        name = parts[i].split(':')[0].replace('label ', '')
        labels[name] = parts[i] + parts[i + 1]
        order.append(name)

    dropped = 0
    for day, scenes in DAYS.items():
        seen = set()
        for scn in scenes:
            if scn not in labels:
                continue
            before = labels[scn].count('\n')
            labels[scn] = dedupe_label(labels[scn], seen)
            after = labels[scn].count('\n')
            if before != after:
                print(f"[dedupe] {scn}: {before - after} duplicate lines removed")
            dropped += before - after

    out = []
    for name in order:
        out.append(labels[name])
    open(path, 'w', encoding='utf-8').write(''.join(out))
    print(f"[dedupe] total: {dropped} lines removed")


if __name__ == '__main__':
    main()
