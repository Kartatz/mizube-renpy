# The classic layout (this project has no screens.rpy) does not use the
# gui.* variables; set its styles directly so Japanese text renders.
init 999 python:
    for st in (style.default, style.say_dialogue, style.say_who_window,
               style.say_label, style.menu_choice, style.menu_choice_chosen,
               style.button, style.button_text, style.main_menu_frame,
               style.input, style.language_switch_button):
        st.font = "fonts/main.ttf"
