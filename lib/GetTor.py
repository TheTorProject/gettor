#!/usr/bin/python
# -*- coding: utf-8 -*-

__program__ = 'GetTor.py'
__url__ = 'https://svn.torproject.org/svn/projects/gettor'
__author__ = 'Jacob Appelbaum <jacob@appelbaum.net>, Christian Fromme <kaner@strace.org>'
__copyright__ = 'Copyright (c) 2008, 2009, The Tor Project'
__license__ = 'See LICENSE for licensing information'

try:
    from future import antigravity
except ImportError:
    antigravity = None

import os
import sys
import logging
import gettor.opt
import gettor.config
import gettor.requests
import gettor.responses
import gettor.utils
import gettor.filters
from time import strftime


def initializeLogging(cfg):
    level = getattr(cfg, 'LOGLEVEL', 'WARNING')
    level = getattr(logging, level)
    extra = {}
    logfileName = cfg.LOGFILE + "-" +  strftime("%Y-%m-%d") + ".log"
    logDir = os.path.join(cfg.BASEDIR, "log")
    if not gettor.utils.createDir(logDir):
        # Fall back to /tmp in case of an error
        logDir="/tmp"
    extra['filename'] = os.path.join(logDir, logfileName)

    print "Logfile is %s" % extra['filename']

    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S",
                        level=level,
                        **extra)

def processFail(conf, rawMessage, failedAction, e=None):
    """This routine gets called when something went wrong with the processing
    """
    logging.error("Failed to " + failedAction)
    if e is not None:
        logging.error("Here is the exception I saw: %s" % sys.exc_info()[0])
        logging.error("Detail: %s" %e)
    if conf.DUMPFILE != "":
        # Keep a copy of the failed email for later reference
        logging.info("We'll keep a record of this mail.")
        dumpFile = os.path.join(conf.BASEDIR, conf.DUMPFILE)
        gettor.utils.dumpMessage(dumpFile, rawMessage)

def processMail(conf):
    """All mail processing happens here. Processing goes as follows:
       - Parse request. This means: Find out everything we need to reply in 
         an appropriate manner. Reply address, language, package name.
         Also try to find out if the user wants split packages and if he has 
         a valid signature on his mail.
       - Do some filtering voodoo.
       - Send reply. Use all information gathered from the request and pass
         it on to the reply class/method to decide what to do.
    """
    rawMessage = ""
    reqInfo = None
    logging.debug("Processing mail..")
    # Retrieve request from stdin and parse it
    try:
        request = gettor.requests.requestMail(conf)
        rawMessage = request.getRawMessage()
        # reqval contains all important information we need from the request
        reqInfo = request.parseMail()
    except Exception as e:
        processFail(conf, rawMessage, "process request", e)
        return False

    # Do some filtering on the request
    try:
        reqInfo = gettor.filters.doFilter(reqInfo)
    except Exception as e:
        processFail(conf, rawMessage, "filter request", e)
        return False

    # See if the filtering process decided if the request was valid
    if reqInfo['valid'] is not True:
        logging.error("Invalid request.")
        processFail(conf, rawMessage, "send reply")
        return False

    # Ok, request information aquired. Make it so.
    try:
        reply = gettor.responses.Response(conf, reqInfo)
        if not reply.sendReply():
            processFail(conf, rawMessage, "send reply")
            return False
        return True
    except Exception as e:
        processFail(conf, rawMessage, "send reply (got exception)", e)
        return False

def processOptions(options, conf):
    """Do everything that's not part of parsing a mail. Prepare GetTor usage,
       install files, fetch packages, do some black/whitelist voodoo and so on
    """ 

    if options.fetchpackages:
        gettor.utils.fetchPackages(conf)
    if options.preppackages:
       gettor.utils.prepPackages(conf)
    if options.installcron:
        gettor.utils.installCron()
    if options.whitelist:
        gettor.utils.addWhitelistEntry(conf, options.whitelist)
    if options.blacklist:
        gettor.utils.addBlacklistEntry(conf, options.blacklist)
    if options.lookup:
        gettor.utils.lookupAddress(conf, options.lookup)
    if options.clearwl:
        gettor.utils.clearWhitelist(conf)
    if options.days:
        gettor.utils.clearBlacklist(conf, options.days)
    if options.cmdpass:
        gettor.utils.setCmdPassword(conf, options.cmdpass)

def main():
    """Parse command line, setup config and logging.
    """
    options, arguments = gettor.opt.parseOpts()
    config = gettor.config.Config(options.configfile)
    initializeLogging(config)

    if sys.stdin.isatty():
        # We separate this because we need a way to know how we reply to the 
        # caller: Send mail/write log file or just dump to stdout/stderr.
        processOptions(options, config)
        print "Done."
    else:
        # We've got mail
        if processMail(config):
            logging.debug("Processing mail finished")
        else:
            logging.error("Processing mail failed")
        logging.debug("Done.")

if __name__ == "__main__":
    main()
