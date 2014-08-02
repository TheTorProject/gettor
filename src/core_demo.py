#!/usr/bin/python
#
# Dummy script to test GetTore's Core module
#

import gettor.core

try:
    core = gettor.core.Core()
    links = core.get_links('dummy service', 'linux', 'es')
    print links
except gettor.core.ConfigurationError as e:
    print "Misconfiguration: " + str(e)
except gettor.core.UnsupportedOSError as e:
    print "Unsupported OS: " + str(e)
except gettor.core.UnsupportedLocaleError as e:
    print "Unsupported Locale: " + str(e)
except gettor.core.InternalError as e:
    print "Internal error: " + str(e)
