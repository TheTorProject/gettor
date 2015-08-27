#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

import gettor.xmpp

def main():
    try:
        bot = gettor.xmpp.XMPP()
        bot.start_bot()
    except gettor.xmpp.ConfigError as e:
        print "Configuration error: %s" % str(e)
    except gettor.xmpp.InternalError as e:
        print "Core module not working: %s" % str(e)
    except Exception as e:
        # in case something unexpected happens
        print "Unexpected error: %s" % str(e)

if __name__ == '__main__':
    main()
