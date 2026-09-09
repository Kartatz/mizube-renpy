#!/usr/bin/env python3
"""add_speakers.py - split speaker-prefixed dialogue into Ren'Py Characters.

The recovered Lingo dialogue embeds the speaker in the string itself, e.g.
"父「飯だ」" (Father: "Dinner."). This tool rewrites game/script.rpy to use
one Character per speaker (Katawa Shoujo: RE convention: a define with
who_color and a translatable name), and writes game/characters.rpy:

    define father = Character(_("父"), who_color="#b07a3f",
                              what_prefix="“", what_suffix="”")

Say lines become:  father "飯だ"

Unprefixed quoted lines (mixed/unknown speakers) remain narrator lines.
"""
import re
import sys

SPEAKERS = {
    "父": ("father", "#b07a3f"),
    "母": ("mother", "#c77fa0"),
    "先生": ("teacher", "#72adee"),
    "教員": ("staff", "#e0e0e0"),
    "父母": ("parents", "#9a8fc0"),
    "生徒": ("student", "#629276"),
    "通行人A": ("passerby_a", "#8899aa"),
    "通行人B": ("passerby_b", "#99aabb"),
}

SAY_RE = re.compile(r'^(    )n "((?:[^"\\]|\\.)*)"$')
PREF_RE = re.compile(
    r'^(' + '|'.join(re.escape(p) for p in sorted(SPEAKERS, key=len, reverse=True)) +
    r')「(.*)」[\s\u3000]*$')


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append(s[i + 1]); i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'game/script.rpy'
    out = []
    converted = 0
    for line in open(path, encoding='utf-8'):
        m = SAY_RE.match(line.rstrip('\n'))
        if m and not line.lstrip().startswith('#'):
            orig = unesc(m.group(2))
            pm = PREF_RE.match(orig)
            if pm:
                var = SPEAKERS[pm.group(1)][0]
                out.append(f'{m.group(1)}{var} "{esc(pm.group(2))}"\n')
                converted += 1
                continue
        out.append(line)
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(out)

    with open('game/characters.rpy', 'w', encoding='utf-8') as f:
        f.write('# Speaker characters (names are translatable via _()).\n')
        f.write('# Style follows the Katawa Shoujo: RE convention:\n')
        f.write('# colored name above the dialogue, curly-quoted speech.\n\n')
        for jp, (var, color) in SPEAKERS.items():
            f.write(f'define {var} = Character(_("{jp}"), who_color="{color}", '
                    f'what_prefix="“", what_suffix="”")\n')
    print(f'[speakers] converted {converted} lines; wrote game/characters.rpy')


if __name__ == '__main__':
    main()
