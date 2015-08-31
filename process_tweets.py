#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

import gettor.twitter

def main():
    """Quick way of running the thing.

    Note that default right now is 'no async', which means, function won't
    return; on the other hand everything "will just work."

    If async is off, then we can:
    >>> from quick_run import quick_run
    >>> bot = quick_run() # authenticate, subscribe to streaming api, get handle
    """

    try:
        bot = TwitterBot()
        bot.authenticate()
        # bot.api.update_status('hello world!')
        bot.subscribeToStreams()
        return bot
    except gettor.twitter.ConfigError as e:
        print "Configuration error: %s" % str(e)
    except gettor.twitter.InternalError as e:
        print "Core module not working: %s" % str(e)
    except Exception as e:
        # in case something unexpected happens
        print "Unexpected error: %s" % str(e)

if __name__ == '__main__':
    main()
