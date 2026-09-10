#!/usr/bin/env python3
"""Fill a Ren'Py translation skeleton (tl/english/script.rpy) from a JSON
dictionary mapping original strings to translations.

Usage:
    python3 tools/fill_translations.py game/tl/english/script.rpy trans.json

Matching is exact first, then whitespace-insensitive (the extracted strings
vary in leading/trailing U+3000 and ASCII spaces between scripts).
Unmatched lines are left untouched and reported.
"""
import json
import re
import sys

SAY_RE = re.compile(r'^(    )([A-Za-z_][A-Za-z0-9_]* )?"((?:[^"\\]|\\.)*)"$')


def normalize(s):
    return s.strip().strip('\u3000').strip()


def esc(s):
    s = s.replace('\\', '\\\\').replace('"', '\\"')
    # escape single [ that are not already part of [[
    return re.sub(r'\[(?!\[)', '[[', s)


def unesc(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append(s[i + 1])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def main():
    tl_path, dict_path = sys.argv[1], sys.argv[2]
    trans = json.load(open(dict_path, encoding='utf-8'))
    norm_map = {}
    for k, v in trans.items():
        norm_map.setdefault(normalize(k), v)

    out = []
    total = filled = 0
    for line in open(tl_path, encoding='utf-8'):
        m = SAY_RE.match(line.rstrip('\n').rstrip('\r'))
        if m and not line.lstrip().startswith('#'):
            total += 1
            indent, speaker, orig = m.group(1), m.group(2) or '', unesc(m.group(3)).replace('[[', '[')

            if orig in trans:
                new = trans[orig]
                filled += 1
            elif normalize(orig) in norm_map:
                new = norm_map[normalize(orig)]
                filled += 1
            else:
                new = orig  # leave untranslated
            out.append(f'{indent}{speaker}"{esc(new)}"\n')
        else:
            out.append(line)
    with open(tl_path, 'w', encoding='utf-8') as f:
        f.writelines(out)
    print(f'[fill] {filled}/{total} say lines translated')
    # report lines still containing Japanese
    import re as _re
    jp = _re.compile(r'[^\x00-\x7f]')
    unmatched = []
    for line in open(tl_path, encoding='utf-8'):
        m = SAY_RE.match(line.rstrip('\n'))
        if m and not line.lstrip().startswith('#') and jp.search(m.group(3)):
            unmatched.append(m.group(3))
    if unmatched:
        print(f'[fill] WARNING: {len(unmatched)} lines still contain Japanese:')
        for u in unmatched[:10]:
            print('   ', u[:60])
    else:
        print('[fill] all say lines translated (or already English)')


if __name__ == '__main__':
    main()


def fill_strings(tl_path, strings_map):
    """Append/patch a `translate <lang> strings:` block with old/new pairs
    (used for translatable character names)."""
    lang = None
    for line in open(tl_path, encoding='utf-8'):
        m = re.match(r'translate (\w+) strings:', line)
        if m:
            lang = m.group(1)
            break
    block = f'\ntranslate {lang or "english"} strings:\n'
    for old, new in strings_map.items():
        block += f'    old "{old}"\n    new "{new}"\n'
    with open(tl_path, 'a', encoding='utf-8') as f:
        f.write(block)
    print(f'[fill] appended {len(strings_map)} string translations')
