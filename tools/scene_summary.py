#!/usr/bin/env python3
"""scene_summary.py - summarize the parsed score per marker range.

For each marker range (marker[i].frame .. marker[i+1].frame-1) collects:
  - background members shown on ch1 (with cast + name)
  - all sprite members used (channel, member, name, geometry) and how many
    frames each appears on
  - sound1/sound2 cues (cast member -> name)
  - frame-script members (the dialogue/logic handlers)

Output: out/scenes.json + out/scenes.txt
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from to_renpy import Cast          # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--score-dir', required=True)
    ap.add_argument('--game', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    d = json.load(open(os.path.join(args.score_dir, 'score_frames.json')))
    frames = d['frames']
    labels = json.load(open(
        os.path.join(args.score_dir, 'markers.json')))['labels']

    # name lookup: lib,member -> name (from the already-resolved dump)
    name_of = {}
    for f in frames:
        for s in f['sprites']:
            name_of.setdefault((s['castLib'], s['member']), s.get('name'))
        for k in ('script', 'sound1', 'sound2', 'transition'):
            v = f['main'][k]
            if v['member']:
                name_of.setdefault((v['castLib'], v['member']), None)

    # fill sound/script names from cgoto/system directly
    casts = {}
    def get_name(lib, member):
        key = (lib, member)
        if key in name_of and name_of[key]:
            return name_of[key]
        fname = {2: 'system', 3: 'cgoto', 4: 'mov', 5: 'mov2', 6: 'mov5',
                 7: 'mov6', 8: 'mov7', 9: 'mov8', 10: 'mov3',
                 11: 'mov4'}.get(lib)
        if not fname:
            return None
        if fname not in casts:
            path = os.path.join(args.game, fname + ('.cxt' if fname in
                                                    ('system', 'cgoto')
                                                    else '.cct'))
            try:
                casts[fname] = Cast(path, fname)
            except Exception:
                casts[fname] = None
        c = casts[fname]
        if c:
            m = c.members.get(member)
            if m:
                name_of[key] = m['name']
                return m['name']
        return None

    ranges = []
    for i, lab in enumerate(labels):
        start = lab['frame']
        end = labels[i + 1]['frame'] if i + 1 < len(labels) else 10 ** 9
        ranges.append((start, end, lab['name']))

    out_txt = open(os.path.join(args.out, 'scenes.txt'), 'w')
    scenes = []
    for start, end, name in ranges:
        sub = [f for f in frames if start <= f['frame'] < end]
        if not sub:
            scenes.append({'marker': name, 'start': start, 'end': end - 1,
                           'frames': 0})
            continue
        bgs = {}
        sprite_use = {}
        sounds = {}
        scripts = {}
        transitions = {}
        for f in sub:
            for s in f['sprites']:
                if s['channel'] == 1:
                    bgs[(s['castLib'], s['member'])] = s.get('name')
                else:
                    k = (s['castLib'], s['member'], s['channel'])
                    e = sprite_use.setdefault(k, {
                        'lib': s['castLib'], 'member': s['member'],
                        'ch': s['channel'], 'name': s.get('name'),
                        'maxw': 0, 'maxh': 0, 'x0': 9999, 'y0': 9999,
                        'x1': -9999, 'y1': -9999, 'frames': 0})
                    e['frames'] += 1
                    e['maxw'] = max(e['maxw'], s['w'])
                    e['maxh'] = max(e['maxh'], s['h'])
                    e['x0'] = min(e['x0'], s['x'] - s['w'] // 2)
                    e['y0'] = min(e['y0'], s['y'] - s['h'] // 2)
                    e['x1'] = max(e['x1'], s['x'] + s['w'] // 2)
                    e['y1'] = max(e['y1'], s['y'] + s['h'] // 2)
            for k in ('sound1', 'sound2'):
                v = f['main'][k]
                if v['member']:
                    nm = get_name(v['castLib'], v['member']) or ''
                    sounds[(v['castLib'], v['member'], nm)] = \
                        sounds.get((v['castLib'], v['member'], nm), 0) + 1
            v = f['main']['script']
            if v['member']:
                nm = get_name(v['castLib'], v['member']) or ''
                scripts[(v['castLib'], v['member'], nm)] = \
                    scripts.get((v['castLib'], v['member'], nm), 0) + 1
            v = f['main']['transition']
            if v['member']:
                nm = get_name(v['castLib'], v['member']) or ''
                transitions[(v['castLib'], v['member'], nm)] = \
                    transitions.get((v['castLib'], v['member'], nm), 0) + 1
        scenes.append({
            'marker': name, 'start': start, 'end': end - 1,
            'nframes': len(sub),
            'bgs': [{'lib': l, 'member': m, 'name': n}
                    for (l, m), n in bgs.items()],
            'sprites': sorted(sprite_use.values(),
                              key=lambda e: (e['ch'], -e['frames'])),
            'sounds': [{'lib': l, 'member': m, 'name': n, 'hits': h}
                        for (l, m, n), h in sorted(sounds.items())],
            'scripts': [{'lib': l, 'member': m, 'name': n, 'hits': h}
                        for (l, m, n), h in sorted(scripts.items())],
            'transitions': [{'lib': l, 'member': m, 'name': n, 'hits': h}
                            for (l, m, n), h in sorted(transitions.items())],
        })

    with open(os.path.join(args.out, 'scenes.json'), 'w') as f:
        json.dump(scenes, f, ensure_ascii=False, indent=1)

    for sc in scenes:
        out_txt.write('#### %s  [frames %d..%d, %d frames]\n' % (
            sc['marker'], sc['start'], sc['end'], sc.get('nframes', 0)))
        for b in sc.get('bgs', []):
            out_txt.write('  BG   lib%d:#%d %s\n' % (
                b['lib'], b['member'], b['name']))
        for s in sc.get('sprites', [])[:40]:
            if s['frames'] < max(2, sc.get('nframes', 0) // 8):
                continue
            out_txt.write('  ch%-3d lib%d:#%-5d %-28s %3dx%3d box=(%d,%d)-(%d,%d) %df\n' % (
                s['ch'], s['lib'], s['member'], (s['name'] or '')[:28],
                s['maxw'], s['maxh'], s['x0'], s['y0'], s['x1'], s['y1'],
                s['frames']))
        for s in sc.get('sounds', [])[:10]:
            out_txt.write('  SND  lib%d:#%d %s (%d)\n' % (
                s['lib'], s['member'], s['name'], s['hits']))
        for s in sc.get('scripts', [])[:12]:
            out_txt.write('  SCR  lib%d:#%d %s (%d)\n' % (
                s['lib'], s['member'], s['name'], s['hits']))
        out_txt.write('\n')
    out_txt.close()
    print('wrote', os.path.join(args.out, 'scenes.txt'),
          'and scenes.json for', len(scenes), 'marker ranges')


if __name__ == '__main__':
    main()
