#!/usr/bin/env python3
"""attribute_speakers.py - scene/heuristic attribution of the unprefixed
quoted dialogue (「...」) to the game's two heroines.

Context: the recovered Lingo dialogue has no explicit speaker metadata.
However the source scripts split cleanly into two story arcs, and speaker
cues (address forms, politeness, speech register) identify who is talking:

  * Yurika arc (home chapters, `case qq1 of` scripts): the step-sister
    speaks casually, addresses the protagonist as お兄ちゃん; the
    protagonist's own speech is imperative/vulgar.
  * Riko arc (school/confinement chapters, `case ssina of` scripts): Riko
    is unfailingly polite (です/ます), addresses the protagonist as 先生;
    the protagonist role-plays as お兄さん/先生 and speaks in imperatives.

Attribution policy:
  - strong cues decide; conflicting/ambiguous lines stay narrator;
  - ellipsis beats stay narrator (silence);
  * in the Riko arc, unmatched speech defaults to Riko (she is the
    speaker of most quoted lines there);
  - in the Yurika arc, unmatched speech stays narrator, except
    home-arrival greetings (ただいま...) which are Yurika's.

Also handles the "教員：" colon-label format found in a few scripts.

Outputs a JSON mapping  original-quoted-string -> {speaker, inner}
and rewrites game/script.rpy accordingly.
"""
import json
import os
import re
import sys

STN = re.compile(r'stn\(\s*"((?:[^"\\]|\\.)*)"\s*(?:,\s*\d+\s*)?\)')
QUOTED = re.compile(r'^「(.*)」[\s\u3000]*$')
ELLIPSIS = re.compile(r'^[.‥…・…\u3000\s]+$')

RKO_MARK = re.compile(r'りこ|先生|治療|罰|教室|授業|机|テスト|成績|誘拐|鎖|手錠|監禁|'
                      r'目隠し|尾行|青山|野田|職員|災害|避難|ボランティア|支援|望月|少女|生徒')
YKA_MARK = re.compile(r'ゆりか|お兄ちゃん')

POLITE = re.compile(r'です。|です、|です？|ですか|ました|ません|ください|ます。|ます、|'
                    r'ます？|ますか|ますから|います')

RIKO_CUES = [
    (POLITE, 'riko'),
    (re.compile(r'^先生[、，]|先生、|^はい、|うけます|お手伝い|がんばります|分かりました|'
                r'違います|言いません|約束します'), 'riko'),
    (re.compile(r'ごめんなさい|すみません|お願いします'), 'riko'),
    (re.compile(r'^[えきしわいじで]え?、|って言ってるのに'), 'riko'),
    (re.compile(r'^いや|いや！|やだ|許して|かないで|帰して'), 'riko'),
    (re.compile(r'んだよ|だろ|かな$|かな？|かい$|かい？|しろ$|してろ|ついて|こい$|座れ|'
                r'動くな|じっとして|騒ぐな|声を出さ|声出さ|入れ|舐め|チ○ポ|マ○コ|犯す|'
                r'射精|精液|いい子|大人しく|お兄さん|りこちゃん|望月|先生の|罰|机に|'
                r'成績|テスト|授業|治療|うん？|そうか|思ってたより|あの娘|媚薬|薬で|'
                r'予防注射|それと同じ|こっち来|近づい|入れて|くわえて'), 'n'),
    (re.compile(r'^だめ|^ダメ'), 'n'),
    (re.compile(r'^うん|^はい$|^はい。|^え？|^えっ'), 'riko'),
    (re.compile(r'？$'), 'riko'),
]
YURIKA_CUES = [
    (re.compile(r'お兄ちゃん'), 'yurika'),
    (re.compile(r'変態|ケダモノ|ロリコン'), 'yurika'),
    (re.compile(r'でしょ|だもん|なんだから|てよね|の？$|のよ$|かよ'), 'yurika'),
    (re.compile(r'^うん|^はい$|^あ、|^きゃ|^え？'), 'yurika'),
    (re.compile(r'^ただいま'), 'yurika'),
    (re.compile(r'んだよ|だろ|かな$|しろ$|してろ|いくぞ|いいか|チ○ポ|犯す|舐め|腰|射精|'
                r'中に|おっぱい|胸|触らせ|くれ|お前|かい[？?]?[\s\u3000]*$|そうか|俺|'
                r'わかるよな|思ってたより|あの娘|薬'), 'n'),
    (re.compile(r'の？$|かな$|かしら'), 'yurika'),
    (re.compile(r'？$'), 'yurika'),
]
ARROW_DEFAULT = {'riko': 'riko', 'yurika': 'n'}


def classify_file(name, text):
    if 'case qq1 of' in text:
        return 'yurika'
    r, y = len(RKO_MARK.findall(text)), len(YKA_MARK.findall(text))
    if r and not y:
        return 'riko'
    if y and not r:
        return 'yurika'
    if r > y:
        return 'riko'
    # no markers: number clusters (1100+ = home arc, the rest = school arc)
    m = re.search(r'(\d+)', name)
    return 'yurika' if m and int(m.group(1)) >= 1000 else 'riko'


def decide(inner, arc):
    if ELLIPSIS.match(inner):
        return 'n'
    cues = RIKO_CUES if arc == 'riko' else YURIKA_CUES
    for rx, who in cues:
        if rx.search(inner):
            return who
    return ARROW_DEFAULT[arc]


def normalize_ws(s):
    return s.strip().strip('\u3000').strip()


def main():
    src_dir = sys.argv[1]
    script = sys.argv[2] if len(sys.argv) > 2 else 'game/script.rpy'

    # 1) decide attribution per source line
    decisions = {}     # normalized original -> speaker (conflicts -> n)
    inner_of = {}       # normalized original -> inner text
    for n in sorted(os.listdir(src_dir)):
        if not n.endswith('.ls'):
            continue
        text = open(os.path.join(src_dir, n), encoding='utf-8', errors='replace').read()
        arc = classify_file(n, text)
        for m in STN.finditer(text):
            orig = m.group(1)
            q = QUOTED.match(orig)
            if not q:
                continue
            inner = q.group(1)
            # colon label format: 「教員：text」
            lab = re.match(r'^(父|母|先生|教員|父母|生徒|通行人A|通行人B)[：:](.*)$', inner)
            if lab:
                key = normalize_ws(orig)
                if key in decisions and decisions[key] != 'staff':
                    decisions[key] = 'n'
                else:
                    decisions[key] = 'staff'
                inner_of[key] = lab.group(2)
                continue
            who = decide(inner, arc)
            key = normalize_ws(orig)
            if key in decisions and decisions[key] != who:
                decisions[key] = 'n'   # conflicting contexts -> narrator
            else:
                decisions[key] = who
            inner_of[key] = inner

    # 2) apply to script.rpy
    SAY_RE = re.compile(r'^(    )n "((?:[^"\\]|\\.)*)"$')
    out = []
    converted = kept_n = 0
    for line in open(script, encoding='utf-8'):
        m = SAY_RE.match(line.rstrip('\n'))
        if m and not line.lstrip().startswith('#'):
            orig = m.group(2).replace('\\', '\\\\').replace('"', '\\"')
            key = normalize_ws(orig)
            who = decisions.get(key)
            if who and who != 'n':
                out.append(f'{m.group(1)}{who} "{inner_of[key]}"\n')
                converted += 1
                continue
            kept_n += 1
        out.append(line)
    with open(script, 'w', encoding='utf-8') as f:
        f.writelines(out)
    print(f'[attribute] converted {converted} quoted lines; {kept_n} remain narrator')
    json.dump({k: {'speaker': v, 'inner': inner_of[k]} for k, v in decisions.items()},
              open('/tmp/opencode/trans/attributions.json', 'w'),
              ensure_ascii=False, indent=0)


if __name__ == '__main__':
    main()
