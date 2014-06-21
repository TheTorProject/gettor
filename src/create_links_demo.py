#!/usr/bin/python
#
# Dummy script to test GetTore's Core module progress
#

import gettor

try:
    core = gettor.Core('gettor.cfg')
    core.create_links_file('Github')
    core.add_link('Github', 'linux', 'es',
                  'https://foo.bar https://foo.bar.asc 111-222-333-444')
    core.add_link('Github', 'linux', 'es',
                  'https://foo.bar https://foo.bar.asc 555-666-777-888')

except ValueError as e:
    print "Value error: " + str(e)
except RuntimeError as e:
    print "Internal error: " + str(e)
