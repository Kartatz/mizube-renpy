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

image ov_face_blink:
    # 13-frame home-scene cycle (mov5 '１_00000…')
    "overlays/mov5_00000.png"
    2.0
    "overlays/mov5_00001.png"
    0.07
    "overlays/mov5_00002.png"
    0.07
    "overlays/mov5_00003.png"
    0.07
    "overlays/mov5_00004.png"
    0.07
    "overlays/mov5_00005.png"
    0.07
    "overlays/mov5_00006.png"
    0.07
    "overlays/mov5_00007.png"
    0.07
    "overlays/mov5_00008.png"
    0.07
    "overlays/mov5_00009.png"
    0.07
    "overlays/mov5_00010.png"
    0.07
    "overlays/mov5_00011.png"
    0.07
    "overlays/mov5_00012.png"
    0.07
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
image ov_sweat = "overlays/mov_ase1.png"       # sweat drop
image ov_grandpa = "overlays/mov2_member0011.png"  # じいさん
image ov_brother = "overlays/mov2_21.png"      # 弟21
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

transform face_pos:
    xalign 0.56
    yalign 0.28

transform face_pos_k1:
    xalign 0.60
    yalign 0.30

transform hand_pos:
    xalign 0.38
    yalign 0.68

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

transform npc_left:
    xalign 0.08
    yalign 0.78

transform npc_right:
    xalign 0.90
    yalign 0.82

# helper labels used by the chapter flow
label overlays_on(mode="blink"):
    if mode == "blink":
        show ov_face_blink at face_pos
    elif mode == "k1":
        show ov_face_k1 at face_pos_k1
    elif mode == "hotel":
        show ov_face_hotel at face_pos
    show screen h_overlay_fx
    show screen icon_bar
    return

label overlays_off():
    hide ov_face_blink
    hide ov_face_k1
    hide ov_face_hotel
    hide screen h_overlay_fx
    hide screen icon_bar
    return
