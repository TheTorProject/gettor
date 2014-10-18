#!/usr/bin/env python
import sys

import gettor.smtp

service = gettor.smtp.SMTP()

# For now we simulate mails reading from stdin
# In linux test as follows:
# $ python smtp_demo.py < email.eml

incoming = sys.stdin.read()
try:
    print "Email received!"
    service.process_email(incoming)
    print "Email sent!"
except gettor.smtp.ConfigError as e:
    print "Misconfiguration: " + str(e)
except gettor.smtp.SendEmailError as e:
    print "SMTP not working: " + str(e)
except gettor.smtp.InternalError as e:
    print "Core module not working: " + str(e)
