# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.

import optparse

__all__ = ["parseOpts"]

def parseOpts():
    cmdParser = optparse.OptionParser()
    cmdParser.add_option("-c", "--config", dest="configfile",
                        default="~/.gettor.conf",
                        help="set config file to FILE", metavar="FILE")
    cmdParser.add_option("-i", "--install-crontab", dest="installcron",
                        action="store_true", default=False,
                        help="install crontab to refresh packagelist")
    cmdParser.add_option("-f", "--fetch-packages", dest="fetchpackages",
                        action="store_true", default=False,
                        help="fetch Tor packages from mirror")
    cmdParser.add_option("-p", "--prep-packages", dest="preppackages",
                        action="store_true", default=False,
                        help="prepare packages (zip them)")
    cmdParser.add_option("-w", "--whitelist", dest="whitelist",
                         default="",
                         help="add an email address to the whitelist",
                         metavar="WHITELIST")
    cmdParser.add_option("-b", "--blacklist", dest="blacklist",
                         default="",
                         help="add an email address to the blacklist",
                         metavar="BLACKLIST")
    cmdParser.add_option("-l", "--lookup", dest="lookup",
                         default="",
                         help="check black/white list presence of address",
                         metavar="CHECKADDRESS")
    cmdParser.add_option("-x", "--clear-whitelist", dest="clearwl",
                        action="store_true", default=False,
                        help="clear all entrys in the whitelist")
    cmdParser.add_option("-y", "--clear-blacklist", dest="days",
                        default=0,
                        help="clear all entrys in the blacklist older than DAYS days")
    cmdParser.add_option("-s", "--set-cmdpassword", dest="cmdpass",
                        default="",
                        help="set the password for mail commands",
                        metavar="CMDPASS")

    return cmdParser.parse_args()
