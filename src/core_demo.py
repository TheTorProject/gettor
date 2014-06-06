#!/usr/bin/python
#
# Dummy script to test GetTore's Core module progress
#

import gettor

try:
    core = gettor.Core('gettor.cfg')
    links = core.get_links('linux', 'en')
    print links
except ValueError as e:
    print "Value error: " + str(e)
except RuntimeError as e:
    print "Internal error: " + str(e)
