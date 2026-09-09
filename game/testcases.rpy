# Automated smoke test (run with: renpy.sh <project> test story)
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
