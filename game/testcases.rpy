testsuite global:
    teardown:
        exit
testcase smoke:
    $ renpy.test.testexecution._test.timeout = 300.0
    $ renpy.change_language("english")
    click "Start" raw
    pause 3.0
    screenshot "smoke_start"
