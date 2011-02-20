# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.

from time import strftime
import logging

__all__ = ["initalize"]

def initialize(cfg):
    level = getattr(cfg, 'LOGLEVEL', 'WARNING')
    level = getattr(logging, level)
    extra = {}
    if getattr(cfg, "LOGFILE"):
        extra['filename'] = cfg.LOGFILE
    else:
        extra['filename'] = "./gettor_log"

    extra['filename'] += "-" +  strftime("%Y-%m-%d") + ".log"
    print "Logfile is %s" % extra['filename']

    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        datefmt="%b %d %H:%M:%S",
                        level=level,
                        **extra)
