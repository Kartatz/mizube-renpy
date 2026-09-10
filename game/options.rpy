# Automatic: project options
define config.name = "mizube (native Ren'Py conversion)"
define config.version = "0.1"
define config.screen_width = 960
define config.screen_height = 720
define config.save_directory = "mizube-renpy"

# Distribution naming (used by the launcher/android builds)
define build.name = "mizube"

init python:
    gui.text_font = "fonts/main.ttf"
    gui.interface_text_font = "fonts/main.ttf"
    gui.name_text_font = "fonts/main.ttf"
    gui.default_font = "fonts/main.ttf"

# Close/quit directly without a confirmation prompt (the minimal
# classic layout this project uses does not provide a yesno screen).
define config.quit_action = Quit(False)
