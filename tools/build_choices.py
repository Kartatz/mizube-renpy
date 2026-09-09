#!/usr/bin/env python3
"""build_choices.py - rebuild the story flow with the recovered choice
menus, branch paths, scenes and animations.

Everything emitted here comes from the decompiled Lingo sources:

  * The 8 choice menus (scripts that write options into button members
    via tl(..., 10/11/12)) and their jump-point setters
    (`選択で飛ぶポイント設定`), which assign the original branch markers
    to xxx/yyy/zzz.
  * Branch dialogue: stn() lines recovered from the source scripts,
    selected per branch by curated file sets and content keywords
    (the exact marker -> frame -> handler mapping needs the Director
    score, which is not yet parsed; the selection basis is documented
    per branch below).
  * Animations: the ATL loops generated from the original cast frame
    sequences (game/animations.rpy).

The result is game/story.rpy: a chapter flow in the Katawa Shoujo: RE
style (menus inline, scene changes with `scene`/`show`, one label per
branch, explicit convergence points matching the original markers).
"""
import json
import os
import re
import sys

SRC = "/tmp/opencode/decomp/casts/system/system/casts/External"
STN = re.compile(r'stn\(\s*"((?:[^"\\]|\\.)*)"\s*(?:,\s*\d+\s*)?\)')
SAY_RE = re.compile(r'^(    )n "((?:[^"\\]|\\.)*)"$')

SPEAKERS = {
    "父": "father", "母": "mother", "先生": "teacher", "教員": "staff",
    "父母": "parents", "生徒": "student", "通行人A": "passerby_a", "通行人B": "passerby_b",
}
PREF_RE = re.compile(r'^(' + '|'.join(sorted(SPEAKERS, key=len, reverse=True)) +
                     r')「(.*)」[\s\u3000]*$')
COLON_RE = re.compile(r'^「(' + '|'.join(sorted(SPEAKERS, key=len, reverse=True)) +
                      r')[：:](.*)」[\s\u3000]*$')
QUOTED_RE = re.compile(r'^「(.*)」[\s\u3000]*$')

# ---------------------------------------------------------------- choices
# (id, lead-in lines shown before the menu, options[(text, branch label)])
CHOICES = [
    dict(id="c1441", lead=["妹はどこ行った。"],
         opts=[("知らないよ。今忙しいから後で俺も探してみるよ", "reply_dunno"),
               ("ゆりかは外出したよ", "reply_out"),
               ("ゆりかとトランプしてるんだ。邪魔しないでよ。", "reply_cards")],
         caption="original: choice 1441, all three replies converge on marker iziru101"),
    dict(id="c554", lead=["なんだ、今夜はご機嫌ななめか？"],
         opts=[("悪かった。実はお前がかわいいと思って…", "reply_cute"),
               ("これは男の「美学」だ。エロい疑惑は一切ない！", "reply_aesth"),
               ("成長していい身体つきになってきたな。", "reply_grown")],
         caption="original: choice 554 -> op15 / op50 / op15"),
    dict(id="c1431", lead=["そっと、ゆっくり扉を開けば気づかれなかっただろう"],
         opts=[("YES", "breakin_yes"), ("NO", "breakin_no")],
         caption="original: choice 1431 -> fn_4 (or opm_v) / cbs8end"),
    dict(id="c1175", lead=["照れくさいけど、これさ、結婚記念プレゼント"],
         opts=[("媚薬の効果を親に教え、少量をプレゼントする", "ohs10"),
               ("結婚記念に「食事＆ホテル宿泊」をプレゼントする", "ohs20"),
               ("俺のコレクション「エロゲー、エロアニメ」を白日の下に晒し、兄妹愛を教育してみる", "ohs30")],
         caption="original: choice 1175 -> ohs10 / ohs20 / ohs30 (three endings)"),
    dict(id="c69", lead=["あの娘だな。思ってたより随分若いな"],
         opts=[("１：りこを誘拐する！", "route_kidnap"),
               ("２：混乱時に学校へ侵入！", "route_school")],
         caption="original: choice 69 -> yukai / fera1 (the route fork of the Riko arc)"),
    dict(id="c550", lead=["誘拐の瞬間を誰かに見られたら‥失敗は許されない‥。"],
         opts=[("YES", "kidnap_go"), ("NO", "kidnap_stop")],
         caption="original: choice 550 -> yuukai-kihon / start"),
    dict(id="c900", lead=["じゃ、まずそこから出て来いよ。"],
         opts=[("舌でぺろぺろしてごらん", "act_lick"),
               ("口にくわえて、しゃぶって", "act_suck")],
         caption="original: choice 900 -> kf08 / kff08"),
    dict(id="c1010", lead=["りこちゃんもいつしか全く抵抗しなくなり、俺のなすがままになっていった。"],
         opts=[("乱暴に強引に", "act_rough"),
               ("優しく誘導しよう", "act_gentle")],
         caption="original: choice 1010 -> iv5_26 / iv5_25"),
]

# ---------------------------------------------------------------- branches
# label -> (original marker, animation, background cast group, content
# selection: list of (files, keywords) - a line is included if it comes
# from one of the files OR matches a keyword; order preserved)
BRANCHES = {
    "reply_dunno":  ("iziru101", None, None, [(["1441"], None)]),
    "reply_out":    ("iziru101", None, None, [(["1441"], None)]),
    "reply_cards": ("iziru101", None, None, [(["1441"], None)]),
    "reply_cute":  ("op15", None, None, [([], ["変態趣味を妹に|こういう時は素直な|お兄ちゃんの嘘つき"])]),
    "reply_aesth": ("op50", None, None, [([], ["美学|え、マジで|エロい疑惑"])]),
    "reply_grown": ("op15", None, None, [([], ["成長していい身体|発育良すぎ|おっぱい"])]),
    "breakin_yes": ("fn_4", "anim_mov_3", "mov",
                    [([], ["家宅侵入|妹部屋の鍵|鍵がかかってない|勝手に部屋に入って|パンツ盗|盗撮って、どんな"])]),
    "breakin_no":  ("cbs8end", None, None, []),
    "ohs10": ("ohs10", "anim_mov_2", "mov5",
              [([], ["媚薬を渡した|旅行日程|媚薬の効果は凄い|数日すれば|両親を排除|好都合"])]),
    "ohs20": ("ohs20", None, "mov6",
              [([], ["結婚記念|温泉旅行|食事＆ホテル|照れくさい|そのうち行かせ|素直に受け取り|一晩中語る"])]),
    "ohs30": ("ohs30", "anim_mov_2", "mov5",
              [([], ["コレクション|白日の下に|エロゲー、エロアニメの中でも|兄と妹が恋におちて|兄妹の禁じられた|神ゲー"])]),
    "route_kidnap": ("yukai", "anim_mov3_1", "mov3",
                     [([], ["誘拐に必要な|誘拐に関する|誘拐場所|誘拐できたなら|監禁場所|四六時中|年齢も住所も|完全犯罪|あの娘だな|手錠を外した|誘拐の瞬間"])]),
    "route_school": ("fera1", "anim_mov2_10", "mov2",
                     [([], ["ボランティア|野田|職員|支援|保護者にも連絡|臨時先生|職員室|学校の惨状|災害後に"])]),
    "kidnap_go": ("yuukai-kihon", "anim_mov3_10", "mov3",
                  [([], ["誘拐の瞬間を絶対|慎重に行動すれば|うまくやれば|誘拐する瞬間さえ|翔来|玄関の扉を開く"])]),
    "kidnap_stop": ("start", None, None, []),
    "act_lick": ("kf08", "anim_mov_2", "mov",
                 [([], ["舌で|ぺろぺろ|舐めるように|なめないと|手をそえる"])]),
    "act_suck": ("kff08", "anim_mov_2", "mov",
                 [([], ["口にくわえて|しゃぶって|奥までくわえて|キャンデー|フェラチオ教えたら|口に入れて"])]),
    "act_rough": ("iv5_26", "anim_mov5_00003", "mov5",
                  [([], ["乱暴に|冷酷に|獣となり|犯し続けた"])]),
    "act_gentle": ("iv5_25", "anim_mov5_00003", "mov5",
                   [([], ["優しく|ゆっくり教え|時間かけて"])]),
}

# confinement + school chapter content (the two big paths)
CHAPTERS = {
    "confinement": ("yukai family", "anim_mov3_1", "mov3",
                    ["ここ、どこ|その鎖は絶対|お父さんお母さんに|それでいい。大人しく|泣いてても|もう俺の言いなり|誘拐されて|外に逃げ|自分の置かれた状況|鎖でつないで|手錠、催涙|自由にりこちゃんという|無理やり犯した|生の本番動画"]),
    "school": ("fera1 family", "anim_mov2_10", "mov2",
               ["テスト|成績|罰を与える|机に手を|治療|病気|予防注射|この薬で|目隠しをして|深呼吸|校内放送|教員「|生徒「|授業|教室|心のケア|おさぼり病"]),
}

ESC_OptionText = {}   # option text -> english (filled below)


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def load_lines():
    """All stn lines in file order with provenance."""
    out = []
    for n in sorted(os.listdir(SRC)):
        if not n.endswith('.ls'):
            continue
        num = re.search(r'(\d+)', n).group(1)
        text = open(os.path.join(SRC, n), encoding='utf-8', errors='replace').read()
        for i, m in enumerate(STN.finditer(text)):
            out.append((num, i, m.group(1)))
    return out


def speaker_line(orig):
    """Attribute a source line to a Ren'Py say statement."""
    if PREF_RE.match(orig):
        m = PREF_RE.match(orig)
        return SPEAKERS[m.group(1)], m.group(2)
    if COLON_RE.match(orig):
        m = COLON_RE.match(orig)
        return SPEAKERS[m.group(1)], m.group(2)
    q = QUOTED_RE.match(orig)
    if q:
        att = json.load(open('/tmp/opencode/trans/attributions.json'))
        d = att.get(orig.strip().strip('\u3000').strip())
        if d and d['speaker'] != 'n':
            return d['speaker'], d['inner']
        return None, q.group(1)
    return None, orig.strip().strip('\u3000').strip()


def select(lines, spec, used):
    """Lines matching (files, keywords) spec, excluding already-used ones."""
    files, keywords = spec
    kws = [re.compile(k) for k in (keywords or [])]
    out = []
    for num, i, orig in lines:
        key = (num, i, orig)
        if key in used:
            continue
        if files and num in files:
            out.append(key)
            used.add(key)
            continue
        for kw in kws:
            if kw.search(orig):
                out.append(key)
                used.add(key)
                break
    return out


# Story-correct art, keyed by the author's own member naming:
#   mov5 '背景オレの部屋' = the protagonist's room background (home arc)
#   mov2 'BG410c' = school background, 'X_3' = park
#   mov3 'eki_*' = the station (stalking), '1_*' = scene 1 (960x720)
#   mov '2_*' = the long H loop, '3_*' = scene 3
#   mov6 'fera1HOTEL_*' = the love-hotel chapter
BG_FRAMES = {
    "mov": "images/mov/2_00000.jpg",
    "mov2": "images/mov2/BG410c.jpg",
    "mov3": "images/mov3/1_00000.jpg",
    "mov5": "images/mov5/member0012.jpg",
    "mov6": "images/mov6/fera1HOTEL_00000.jpg",
}


def emit_says(out, keys, lines_index):
    for (num, i, orig) in keys:
        who, text = speaker_line(orig)
        t = esc(text)
        if who:
            out.append(f'    {who} "{t}"')
        else:
            out.append(f'    n "{t}"')


def main():
    lines = load_lines()
    lines_index = {(num, i): orig for num, i, orig in lines}
    used = set()

    # don't re-emit lines already in scene labels (the qq1 chapters)
    # (scene labels keep their content; branches only take misc lines)
    out = []
    w = out.append
    w('# game/story.rpy - generated by tools/build_choices.py')
    w('#')
    w('# Story flow with the recovered choice menus, branch paths, scenes')
    w('# and animations. Choice options and branch jump targets are exact')
    w('# (from the decompiled choice and jump-point scripts); branch dialogue')
    w('# is selected from the recovered stn() lines by content, since the')
    w('# marker -> frame -> handler mapping needs the Director score.')
    w('')
    w('label story_flow:')
    w('    call chapter_opening')
    w('    # ---- the home arc, structured as the original day chapters')
    w('    call chapter_day1')
    w('    n "■翌日■"')
    w('    call chapter_day2')
    w('    n "■数日後■"')
    w('    call chapter_day3')
    w('    n "■６日後■"')
    w('    call chapter_day4')
    w('    call overlays_off()')
    w('    # ---- choice 1441: father asks about Yurika (converges: iziru101)')
    for l in ['妹はどこ行った。']:
        w(f'    n "{esc(l)}"')
    w('    menu c1441:')
    for text, label in CHOICES[0]['opts']:
        w(f'        "{esc(text)}":')
        w(f'            call {label}')
    w('    # ---- choice 554: reply to Yurika (op15 / op50 / op15)')
    for l in ['なんだ、今夜はご機嫌ななめか？']:
        w(f'    n "{esc(l)}"')
    w('    menu c554:')
    for text, label in CHOICES[1]['opts']:
        w(f'        "{esc(text)}":')
        w(f'            call {label}')
    w('    # ---- choice 1431: break-in confirm (fn_4|opm_v / cbs8end)')
    for l in ['そっと、ゆっくり扉を開けば気づかれなかっただろう']:
        w(f'    n "{esc(l)}"')
    w('    menu c1431:')
    w('        "YES":')
    w('            call breakin_yes')
    w('        "NO":')
    w('            call breakin_no')
    w('    # ---- choice 1175: anniversary gift (ohs10 / ohs20 / ohs30)')
    for l in ['照れくさいけど、これさ、結婚記念プレゼント']:
        w(f'    n "{esc(l)}"')
    w('    menu c1175:')
    for text, label in CHOICES[3]['opts']:
        w(f'        "{esc(text)}":')
        w(f'            call {label}')
    w('    call chapter_rico_intro')
    w('    # ---- choice 69: the route fork (yukai / fera1)')
    w('    menu c69:')
    w('        "１：りこを誘拐する！":')
    w('            call route_kidnap')
    w('            # ---- choice 550: kidnapping confirm (yuukai-kihon / start)')
    w('            menu c550:')
    w('                "YES":')
    w('                    call kidnap_go')
    w('                    call chapter_confinement')
    w('                "NO":')
    w('                    call kidnap_stop')
    w('                    return')
    w('        "２：混乱時に学校へ侵入！":')
    w('            call route_school')
    w('            call chapter_school')
    w('            # ---- choice 900: lick / suck (kf08 / kff08)')
    w('            menu c900:')
    w('                "舌でぺろぺろしてごらん":')
    w('                    call act_lick')
    w('                "口にくわえて、しゃぶって":')
    w('                    call act_suck')
    w('            # ---- choice 1010: rough / gentle (iv5_26 / iv5_25)')
    w('            menu c1010:')
    w('                "乱暴に強引に":')
    w('                    call act_rough')
    w('                "優しく誘導しよう":')
    w('                    call act_gentle')
    w('    call chapter_end')
    w('    return')
    w('')
    # chapters ---------------------------------------------------------
    w('label chapter_opening:')
    w('    scene black')
    w('    show expression "images/mov5/member0012.jpg" as bg')
    w('    with fade')
    intro = select(lines, ([], ["これが最近一緒に|妹といっても父の再婚|最初は人見知り|突然、この見知らぬ少女|PCからジャック"]), used)
    emit_says(out, intro, lines_index)
    w('    return')
    w('')
    # ---- day-structured home arc (qq1 chapters)
    days = [
        ('day1', [10, 15, 18], 'images/mov5/member0012.jpg', None),
        ('day2', [20, 21, 25, 27, 30, 34], 'images/mov2/X_3.jpg', None),
        ('day3', [37, 39, 40, 42], 'images/mov3/1_00000.jpg', 'anim_mov3_1'),
        ('day4', [50, 51, 52, 54, 55, 60], 'images/mov/2_00000.jpg', 'anim_mov_2'),
    ]
    for name, qqs, bg, anim in days:
        w(f'label chapter_{name}:')
        w(f'    scene black')
        w(f'    show expression "{bg}" as bg')
        w('    with fade')
        if name in ('day1', 'day2'):
            w('    show ov_face_blink at face_pos')
        else:
            w('    call overlays_on("k1")')
        if name == 'day2':
            # the wandering family (readme: "the girl's family will
            # wander around nearby - if you aren't careful, they catch on")
            w('    show ov_grandpa at npc_left')
            w('    show ov_brother at npc_right')
        if anim:
            w(f'    show {anim} as act')
        for qq in qqs:
            w(f'    call scene_{qq:03d}')
        if name in ('day3', 'day4'):
            w('    call overlays_off()')
        w('    return')
        w('')
    w('label chapter_rico_intro:')
    w('    hide act')
    w('    scene black')
    w('    show expression "images/mov3/eki_00000.jpg" as bg')
    w('    with fade')
    intro2 = select(lines, ([], ["あの娘だな|年齢も住所も|通学路なら|人目に付かない場所|誘拐する瞬間さえ|完全犯罪ができる"]), used)
    emit_says(out, intro2, lines_index)
    w('    return')
    w('')
    w('label chapter_end:')
    ending = select(lines, ([], ["災害は起こった|崩壊するはず|普通の兄妹|家庭そして社会|幸せだった|獣となり"]), used)
    emit_says(out, ending, lines_index)
    w('    n "— end of converted scenario —"')
    w('    return')
    w('')

    # branches -----------------------------------------------------------
    for label, (marker, anim, bg, specs) in BRANCHES.items():
        w(f'# branch {label}: original marker "{marker}"')
        w(f'label {label}:')
        if not anim:
            w('    hide act')
        if bg:
            w(f'    scene black')
            w(f'    show expression "{BG_FRAMES[bg]}" as bg')
            w('    with fade')
        if label == 'ohs20':
            w('    call overlays_on("hotel")')
        if anim:
            w(f'    show {anim} as act')
        keys = []
        for spec in specs:
            keys += select(lines, spec, used)
        if not keys:
            w(f'    $ pass  # (original converges immediately: marker {marker})')
        else:
            emit_says(out, keys, lines_index)
        w('    return')
        w('')

    # big paths ----------------------------------------------------------
    for label, (doc, anim, bg, keywords) in CHAPTERS.items():
        w(f'# chapter {label}: {doc}')
        w(f'label chapter_{label}:')
        w('    call overlays_on("k1")')
        if bg:
            w(f'    scene black')
            w(f'    show expression "{BG_FRAMES[bg]}" as bg')
            w('    with fade')
        if anim:
            w(f'    show {anim} as act')
        keys = select(lines, ([], keywords), used)
        emit_says(out, keys, lines_index)
        w('    call overlays_off()')
        w('    return')
        w('')

    with open('game/story.rpy', 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print(f'[choices] wrote game/story.rpy ({len(out)} lines)')


def emit_menu(out, choice, indent=''):
    if choice['lead']:
        for l in choice['lead']:
            out.append(f'{indent}n "{esc(l)}"')
    out.append(f'{indent}menu {choice["id"]}:')
    for text, label in choice['opts']:
        out.append(f'{indent}    "{esc(text)}":')
        out.append(f'{indent}        call {label}')
    out.append(f'{indent}# {choice["caption"]}')


if __name__ == '__main__':
    main()
