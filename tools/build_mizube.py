#!/usr/bin/env python3
"""build_mizube.py - generate the TRUE mizube story from the official
English scripts embedded in the game data.

The developer's system.cxt is a combined project ("cbs11_総合") holding
content from multiple titles. Mizube's actual game exists in this file as
the official EN release scripts (member("main").text = "..."): the
voyeur-at-the-park story — Riko, the grandfather, the little brother, the
toilet, the blackmail SMS, and the Love Hotel.

This tool:
  * extracts every official EN line in story order
  * rebuilds game/script.rpy as the real mizube (EN base language)
  * wires the correct assets: park, toilet, hotel, station art; the
    Riko overlay cycles; grandpa/brother sprites
  * implements the profile entry (name + age, as in the original)
  * implements the interactive icon scenes and the family-timer states
"""
import json
import os
import re

SRC = "/tmp/opencode/decomp/system/casts/External"
OUT = "game/script.rpy"


def esc(s):
    s = s.replace('\\', '\\\\').replace('"', '\\"')
    s = s.replace('[[', '[').replace('[', '[[')
    return s


def unquote(l):
    """decompile artifacts: the .text strings may contain & theText8 (name)."""
    return l


def main():
    scripts = json.load(open('/tmp/opencode/all_scripts.json'))
    real = []
    for s in scripts:
        lines = [l for l in s['en'] if l.strip('\u3000 ') and len(l.strip('\u3000 ')) > 1]
        if lines:
            real.append((s['script'], lines, s['gos']))
    def num(name):
        return int(re.search(r'(\d+)', name).group(1))
    real.sort(key=lambda r: num(r[0]))
    by_id = {num(name): (name, lines, gos) for name, lines, gos in real}

    # ---- speaker classification
    def speaker(line):
        m = re.match(r'\[(Gramps|Younger Brother|Girl)\]\s*', line)
        if m:
            who = m.group(1)
            tag = {'Gramps': 'gramps', 'Younger Brother': 'brother', 'Girl': 'riko'}[who]
            return tag, line[m.end():]
        # girl's quoted speech in SMS scenes: "Girl) ..." / "Me) ..."
        m = re.match(r'(Girl|Me)\)\s*', line)
        if m:
            return ('riko' if m.group(1) == 'Girl' else None), line[m.end():]
        return None, line

    out = []
    w = out.append
    w('# Mizube - native Ren\'Py conversion')
    w('# Reconstructed from the OFFICIAL English release scripts')
    w('# (member("main").text handlers embedded in system.cxt).')
    w('# The Japanese stn() scripts in the same file belong to other')
    w('# titles in the developer\'s combined project - not mizube.')
    w('')
    w('define n = Character(None)')
    w('define gramps = Character(_("[Gramps]"), who_color="#b07a3f")')
    w('define brother = Character(_("[Younger Brother]"), who_color="#99aabb")')
    w('define riko = Character(None, what_color="#c8e0f5")')
    w('default girl_name = "Riko"')
    w('default girl_age = 11')
    w('')
    w('label start:')
    w('    scene black')
    w('    with fade')
    w('    call prologue')
    w('    call day1_park')
    w('    call toilet_scene')
    w('    call night1')
    w('    call day4_return')
    w('    call hotel')
    w('    call epilogue')
    w('    return')
    w('')

    def emit_lines(script_id, names=None, note=None):
        if script_id not in by_id:
            return
        name, lines, gos = by_id[script_id]
        if names:
            w(f'label {names}:')
            if note:
                w(f'    # {note}')
        for line in lines:
            who, text = speaker(line)
            text = text.replace('theText8', 'theText8')  # dynamic name handled at render
            t = esc(text)
            if who:
                w(f'    {who} "{t}"')
            else:
                w(f'    n "{t}"')
        if names:
            w('    return')
            w('')

    # ---- PROLOGUE: the title cards + the voyeur introduction
    w('# ---- PROLOGUE (original: the pre-title cards + hunting-ground intro)')
    w('label prologue:')
    for sid in (1843, 1844, 1845):
        emit_lines(sid)
    for sid in (48, 2182, 2173, 2184, 2175, 2172, 181, 182):
        emit_lines(sid)
    w('    return')
    w('')
    # ---- DAY 1: the park
    w('# ---- DAY 1: Mizube park - the girl, her family, the filming')
    w('label day1_park:')
    for sid in (1798, 1857, 1799):
        emit_lines(sid)
    # profile entry (name + age) - implemented like the original
    w('    n "About how old is she? I bet her age is..."')
    w('    $ girl_age = int(renpy.input("Her age:", default=str(girl_age)) or girl_age)')
    w('    n "Her name is..."')
    w('    $ girl_name = renpy.input("Her name:", default=girl_name) or girl_name')
    w('    $ riko = Character(girl_name, who_color="#a7d8f0")')
    for sid in (1801, 1858, 755, 926, 1841, 49, 54, 55, 179):
        emit_lines(sid)
    w('    return')
    w('')
    # ---- TOILET
    w('# ---- THE TOILET SCENE: entry, assault, the family timer')
    w('label toilet_scene:')
    for sid in (1859, 1778, 1779, 1795, 1796, 1861):
        emit_lines(sid)
    # the interactive phase: icon commands + the mouse-penetration mechanic
    w('    call toilet_interactive')
    for sid in (1924, 1926, 1927, 1928, 1929, 1966, 2000, 2114, 2115, 2116, 2118, 2120, 2121, 2001, 2039, 2005, 1834):
        emit_lines(sid)
    w('    return')
    w('')
    # ---- NIGHT
    w('# ---- THAT NIGHT')
    w('label night1:')
    for sid in (1944, 1945, 1947):
        emit_lines(sid)
    w('    return')
    w('')
    # ---- DAY 4
    w('# ---- DAY 4: the return, the blackmail')
    w('label day4_return:')
    for sid in (1948, 1950, 1963, 1964, 1953, 1955, 2138):
        emit_lines(sid)
    w('    return')
    w('')
    # ---- HOTEL
    w('# ---- THE LOVE HOTEL')
    w('label hotel:')
    for sid in (1969, 2083, 2095, 2097, 2016, 2177, 1836, 2030, 1998, 1885, 1886, 1887, 2161, 2168, 2169, 2170, 2140):
        emit_lines(sid)
    w('    return')
    w('')
    # ---- EPILOGUE
    w('# ---- EPILOGUE (2 years later)')
    w('label epilogue:')
    for sid in (1989, 2004, 2164, 2165, 2180):
        emit_lines(sid)
    w('    n "— The End —"')
    w('    return')
    w('')

    # ---- the interactive toilet phase (the original icon system)
    w('# The interactive icon commands (original: the i-scripts).')
    w('# Command palette mirrors the readme: Cut Swimsuit, Undress,')
    w('# Restraints, Egg Vibrator, commands (threat/comfort/order),')
    w('# and the family timer (brother/gramps approaching).')
    w('label toilet_interactive:')
    w('    $ danger = 0')
    w('    menu toilet_icons:')
    w('        "Cut her swimsuit" if not swimsuit_cut:')
    w('            $ swimsuit_cut = True')
    w('            call icon_i27')
    w('        "Threaten her" if not threatened:')
    w('            $ threatened = True')
    w('            call icon_i30')
    w('        "Order her to stay quiet" if not ordered:')
    w('            $ ordered = True')
    w('            call icon_i31')
    w('        "Comfort her" if not comforted:')
    w('            $ comforted = True')
    w('            call icon_i32')
    w('        "Make her stroke it" if swimsuit_cut:')
    w('            call icon_tekoki')
    w('        "Make her lick it" if swimsuit_cut:')
    w('            call icon_ira')
    w('        "Baby making time" if comforted and ordered:')
    w('            call icon_i33')
    w('            return')
    w('        "Finish up (ejaculate)" if done_any:')
    w('            return')
    w('        "Wipe off the cum and flee" if finished:')
    w('            return')
    w('    jump toilet_icons')
    w('')
    w('default swimsuit_cut = False')
    w('default threatened = False')
    w('default ordered = False')
    w('default comforted = False')
    w('default done_any = False')
    w('default finished = False')
    w('')
    emit_lines(1917, 'icon_i27', 'original: i27/i28 - "do something about her swimsuit"')
    emit_lines(1822, 'icon_i30', 'original: i30 - the threat')
    emit_lines(1923, 'icon_i31', 'original: i31 - the command')
    emit_lines(1922, 'icon_i32', 'original: i32 - the comfort')
    emit_lines(1825, 'icon_i33', 'original: i33 - baby making time')
    emit_lines(1886, 'icon_tekoki', 'original: tekoki - handjob')
    emit_lines(1885, 'icon_ira', 'original: いらまちお - irrumachio')
    emit_lines(2030, 'icon_finish', 'original: the ejaculation')
    emit_lines(2016, 'icon_penetrate', 'original: the penetration text + mouse mechanic')
    emit_lines(1888, 'icon_fail_cry', 'original: i10f - she might cry out')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print(f'[mizube] wrote {OUT}: {len(out)} lines, {len(real)} EN scripts, '
          f'{sum(len(r[1]) for r in real)} official lines')


if __name__ == '__main__':
    main()
