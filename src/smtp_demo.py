#!/usr/bin/env python
import sys

import smtp

service = smtp.SMTP('smtp.cfg')

# For now we simulate mails reading from stdin
# In linux test as follows:
# $ python smtp_demo.py < email.eml

incoming = sys.stdin.read()
try:
    print "Email received!"
    service.process_email(incoming)
    print "Email sent!"
except ValueError as e:
    print "Value error: " + str(e)
except RuntimeError as e:
    print "Runtime error: " + str(e)
