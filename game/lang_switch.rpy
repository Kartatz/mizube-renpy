# Language switcher for the mizube conversion.
#
# The base script language is Japanese (the original game text); the
# English translation lives in game/tl/english/. This screen provides a
# small always-visible selector so the language can be switched from the
# main menu, the game menu, or during play.
#
# Ren'Py ships everything needed: the Language action (00action_other.rpy)
# and the tl/ translation framework.

init python:
    # register the available languages (shown by renpy's own tooling too)
    config.translations = [
        ("English", "english"),
        ("日本語", None),
    ]
    # show the switcher on the main menu, the game menu, and in-game
    config.always_shown_screens.append("lang_switch")


screen lang_switch():
    vbox:
        xalign 0.985
        yalign 0.02
        spacing 2

        textbutton "English" action Language("english"):
            style "lang_switch_button"

        textbutton "日本語" action Language(None):
            style "lang_switch_button"


style lang_switch_button:
    xalign 1.0
    right_padding 8
    left_padding 8

style lang_switch_button is button:
    background None
    hover_background "#00000080"
    size 16
