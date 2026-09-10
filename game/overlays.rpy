# Overlay sprite layer: the recovered Director overlay system.
#
# * Blink/expression cycles  - the original 瞬き (blink) system
#   (MovieScript 210 - 瞬き基本): the heroine's face patch animates over
#   the same-scene background, exactly as the Director score composited it.
# * Body-part/effect sprites - the protagonist's hand (ore0), saliva,
#   sweat, mouth overlays from the mov/mov2 casts.
# * NPC sprites              - the grandpa / little brother that wander
#   near the toilet (the readme's "family will catch on" mechanic).

# ---------------------------------------------------------------- cycles

image ov_face_home:
    # 12-frame home-arc H cycle (mov5 '１_00000…')
    block:
        "overlays/mov5_00000.png"
        0.10
        "overlays/mov5_00001.png"
        0.10
        "overlays/mov5_00002.png"
        0.10
        "overlays/mov5_00003.png"
        0.10
        "overlays/mov5_00004.png"
        0.10
        "overlays/mov5_00005.png"
        0.10
        "overlays/mov5_00006.png"
        0.10
        "overlays/mov5_00007.png"
        0.10
        "overlays/mov5_00008.png"
        0.10
        "overlays/mov5_00009.png"
        0.10
        "overlays/mov5_00010.png"
        0.10
        "overlays/mov5_00011.png"
        0.10
        repeat

image ov_day2_head:
    # the day-2 home head patch (mov5 'day2h'): two states alternating
    "overlays/mov5_day2h.png"
    1.5
    "overlays/mov5_day2h2.png"
    1.5
    repeat


image ov_face_k1:
    # 13-frame expression cycle (mov3 'k1_…')
    block:
        "overlays/mov3_k1_00000.png"
        0.09
        "overlays/mov3_k1_00001.png"
        0.09
        "overlays/mov3_k1_00002.png"
        0.09
        "overlays/mov3_k1_00003.png"
        0.09
        "overlays/mov3_k1_00004.png"
        0.09
        "overlays/mov3_k1_00005.png"
        0.09
        "overlays/mov3_k1_00006.png"
        0.09
        "overlays/mov3_k1_00007.png"
        0.09
        "overlays/mov3_k1_00008.png"
        0.09
        "overlays/mov3_k1_00009.png"
        0.09
        "overlays/mov3_k1_00010.png"
        0.09
        "overlays/mov3_k1_00011.png"
        0.09
        "overlays/mov3_k1_00012.png"
        0.09
        repeat

image ov_face_hotel:
    # 13-frame love-hotel state cycle (mov6 'fera1HOTEL_…')
    block:
        "overlays/mov6_fera1HOTEL_00000.png"
        0.10
        "overlays/mov6_fera1HOTEL_00001.png"
        0.10
        "overlays/mov6_fera1HOTEL_00002.png"
        0.10
        "overlays/mov6_fera1HOTEL_00003.png"
        0.10
        "overlays/mov6_fera1HOTEL_00004.png"
        0.10
        "overlays/mov6_fera1HOTEL_00005.png"
        0.10
        "overlays/mov6_fera1HOTEL_00006.png"
        0.10
        "overlays/mov6_fera1HOTEL_00007.png"
        0.10
        "overlays/mov6_fera1HOTEL_00008.png"
        0.10
        "overlays/mov6_fera1HOTEL_00009.png"
        0.10
        "overlays/mov6_fera1HOTEL_00010.png"
        0.10
        "overlays/mov6_fera1HOTEL_00011.png"
        0.10
        "overlays/mov6_fera1HOTEL_00012.png"
        0.10
        repeat

# ---------------------------------------------------------------- sprites

image ov_hand = "overlays/mov2_ore0.png"       # the protagonist's hand
image ov_saliva = "overlays/mov_2_2.png"       # 唾液2
image ov_sweat = "overlays/mov_ase1.png"      # sweat drop
image ov_grandpa = "overlays/mov2_member0011.png"  # じいさん
image ov_brother = "overlays/mov2_21.png"     # 弟21
image ov_girl = "overlays/mov2_2.png"         # the girl ('2', 154x524)
image ov_key = "overlays/system_key.png"
image ov_rope_art = "overlays/system_roop.png"
image ov_drug_art = "overlays/system_biyaku.png"

# ---------------------------------------------------------------- effects
# The icon-driven overlay states (the interactive-mode icon system).

default ov_rope = False
default ov_drug = False
default ov_hand = False

screen h_overlay_fx():
    if ov_rope:
        add "ov_rope_art" at fx_rope
    if ov_drug:
        add "ov_saliva" at fx_saliva
        add "ov_sweat" at fx_sweat
        add "ov_sweat" at fx_sweat2
    if ov_hand:
        add "ov_hand" at fx_hand

screen icon_bar():
    # The recovered interactive-mode icons (key/rope/aphrodisiac/hand),
    # toggling the overlay states just like the original icon screen.
    hbox:
        xalign 0.97
        yalign 0.94
        spacing 4
        imagebutton idle "overlays/system_te2.png" action ToggleVariable("ov_hand")
        imagebutton idle "overlays/system_roop.png" action ToggleVariable("ov_rope")
        imagebutton idle "overlays/system_biyaku.png" action ToggleVariable("ov_drug")

# ---------------------------------------------------------------- positions
# Score-verified placements (tools/parse_score.py on the embedded movie's
# VWSC). Director sprite loc = the member's reg point: center for the
# stage art/sprites, top-left for the system icon bitmaps (the icon grid
# tiles at x=5/151/224/297, y=340/435/530 prove top-left anchoring).

transform face_pos:
    xalign 0.5
    yalign 0.5

transform face_pos_k1:
    xalign 0.5
    yalign 0.5

transform hand_pos:
    xalign 0.38
    yalign 0.68

# ore0 (the protagonist's hand) in the b20 toilet interactive:
# 312x404 at (400,430) center -> top-left (244,228)
transform ore0_pos:
    xpos 244
    ypos 228

# ore0 thrust zoom (b24_end): scaled to 564x830 at (280,470)
# -> top-left (-2,55)
transform ore0_thrust:
    xpos -2
    ypos 55
    zoom 1.8

# grandpa in the park camera scene (a01): 83x212 at (260,370)
# -> top-left (219,264)
transform grandpa_park_pos:
    xpos 219
    ypos 264

# the girl (mov2 '2', 154x524) in the park family view (score frame
# 1115, the "She turned around..." beat): centered (410,463)
# -> top-left (333,201)
transform girl_park_pos:
    xpos 333
    ypos 201

# brother in the park family view: 35x69 at (227,416)
# -> top-left (210,382)
transform brother_park_pos:
    xpos 210
    ypos 382

# brother waiting outside the toilet (2day1): 35x69 at (867,563)
# -> top-left (850,529)
transform brother_toilet_pos:
    xpos 850
    ypos 529

# the viewfinder edge strip: 350x720 at (687,360) -> top-left (512,0)
transform viewfinder_pos:
    xpos 512
    ypos 0

transform fx_hand:
    xalign 0.42
    yalign 0.55

transform fx_rope:
    xalign 0.56
    yalign 0.42
    zoom 1.6

transform fx_saliva:
    xalign 0.52
    yalign 0.62

transform fx_sweat:
    xalign 0.40
    yalign 0.30

transform fx_sweat2:
    xalign 0.66
    yalign 0.34

transform day2_head_pos:
    xalign 0.22
    yalign 0.62

transform npc_left:
    xalign 0.08
    yalign 0.78

transform npc_right:
    xalign 0.90
    yalign 0.82

# ---------------------------------------------------------------- icon bars
# The original's interactive-mode icon systems, at the exact score
# coordinates. Toilet (marker b20, frames 1639-1742): i21/i22/i23 at
# y~526, x = 163/86/8 (top-left anchored, 70x70 each). Love hotel
# (marker fera01, frames 3796-3814): a 2x3+1 grid.

screen toilet_icons_bar():
    # i21 = restraint, i22 = aphrodisiac, i23 = escape/quit
    hbox:
        spacing 13
        xpos 8
        ypos 525
        imagebutton idle "overlays/system_i22.png" hover "overlays/system_i22_2.png" action ToggleVariable("ov_drug")
        imagebutton idle "overlays/system_i21.png" hover "overlays/system_i21_2.png" action NullAction()
    imagebutton:
        xpos 8
        ypos 435
        idle "overlays/system_i23.png"
        hover "overlays/system_i23_2.png"
        action Return("escape")

screen hotel_icons_bar(cmd=None):
    # the fera01 grid: i36 exit, i10 threaten, i11 command, i10f forbid-cry,
    # tekoki handjob, tekokiS handjob-fast, いらまちお irrumachio
    imagebutton:
        xpos 5 ypos 530
        idle "overlays/system_i36.png" hover "overlays/system_i36_2.png"
        action Return("leave")
    imagebutton:
        xpos 151 ypos 340
        idle "overlays/system_i10.png" hover "overlays/system_i10_2.png"
        action Return("threat")
    imagebutton:
        xpos 151 ypos 434
        idle "overlays/system_i11.png" hover "overlays/system_i11_2.png"
        action Return("command")
    imagebutton:
        xpos 224 ypos 340
        idle "overlays/system_i10f.png" hover "overlays/system_i10f_2.png"
        action Return("quiet")
    imagebutton:
        xpos 224 ypos 435
        idle "overlays/system_tekoki.png" hover "overlays/system_tekoki_2.png"
        action Return("tekoki")
    imagebutton:
        xpos 297 ypos 340
        idle "overlays/system_member1885.png" hover "overlays/system_member1885_2.png"
        action Return("ira")
    imagebutton:
        xpos 297 ypos 435
        idle "overlays/system_tekokiS.png" hover "overlays/system_tekokiS_2.png"
        action Return("tekoki_fast")

# helper labels used by the chapter flow
label overlays_on(mode="home"):
    if mode == "home":
        show ov_face_home at face_pos
    elif mode == "k1":
        show ov_face_k1 at face_pos_k1
    elif mode == "hotel":
        show ov_face_hotel at face_pos
    show screen h_overlay_fx
    show screen icon_bar
    return

label overlays_off():
    hide ov_face_home
    hide ov_day2_head
    hide ov_face_k1
    hide ov_face_hotel
    hide screen h_overlay_fx
    hide screen icon_bar
    return
