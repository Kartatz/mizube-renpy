# The choice menu screen (KS:RE style).
#
# Without this screen the classic layout renders menu choices inline in
# the say window. Ren'Py's display_menu uses the "choice" screen when it
# exists — a separate centered menu box above the dialogue, like
# Katawa Shoujo: RE's implementation (game/screens.rpy: screen choice).

screen choice(items):
    style_prefix "choice"

    vbox:
        for i in items:
            textbutton i.caption action i.action


style choice_vbox is vbox:
    align (0.5, 0.35)
    spacing 8

style choice_button:
    xpadding 24
    ypadding 6
    background Frame(Solid("#102030b0"), 6, 6)
    hover_background Frame(Solid("#305070d0"), 6, 6)
    xalign 0.5

style choice_button_text:
    color "#ffffff"
    hover_color "#ffe090"
    outlines [ (1, "#000000", 0, 0) ]
    xalign 0.5
