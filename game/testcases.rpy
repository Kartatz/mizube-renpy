# Automated smoke tests (run with: renpy.sh <project> test <testcase>)
testsuite global:
    teardown:
        exit

testcase story:
    $ renpy.test.testexecution._test.timeout = 300.0
    click "Start" raw
    pause 3.0
    screenshot "menu_to_story"
    pause 3.0
    screenshot "story_line2"

testcase story_english:
    $ renpy.test.testexecution._test.timeout = 300.0
    $ renpy.change_language("english")
    click "Start" raw
    pause 3.0
    screenshot "english_story"
