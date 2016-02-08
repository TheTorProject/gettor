#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

import gettor.twitter

def main():
    logging_level = 'DEBUG'
    logging_file = '/home/ilv/Proyectos/tor/gettor/log/process_tweets.log'
    logging_format = '[%(levelname)s] %(asctime)s - %(message)s'
    date_format = "%Y-%m-%d" # %H:%M:%S

    logging.basicConfig(
        format=logging_format,
        datefmt=date_format,
        filename = logging_file,
        level = logging_level
    )

    logging.debug("Starting bot")
    try:
        bot = gettor.twitter.TwitterBot()
        bot.start()
    except gettor.twitter.ConfigError as e:
        logging.error("Configuration error: %s" % str(e))
    except gettor.twitter.InternalError as e:
        logging.error("Core module not working: %s" % str(e))
    except Exception as e:
        # in case something unexpected happens
        logging.error("Unexpected error: %s" % str(e))

if __name__ == '__main__':
    main()
