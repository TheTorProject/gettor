# Copyright (c) 2008 - 2011, Jacob Appelbaum <jacob@appelbaum.net>, 
#                            Christian Fromme <kaner@strace.org>
#  This is Free Software. See LICENSE for license information.
'''
 Note that you can set from none to any of these values in your config file.
 Values you dont provide will be taken from the defaults in 'CONFIG_DEFAULTS'.

 Here is what each of them is used for individually:

 MAIL_FROM:     The email address we put in the `from' field in replies.
 BASEDIR:       Where it is all based at. Subdirs for GetTor start from here.
 LOGFILE:       Log messages will be written to $logFile-YYYY-MM-DD.log
 LOGLEVEL:      The level log records are written with
 DELAY_ALERT:   If set to True (the default), a message will be sent to any
                user who has properly requested a package. The message confirms
                that a package was selected and will be sent.
 PASSFILE:      Where our forward command password resides
 DUMPFILE:      Where failed mails get stored
 BLACKLIST_BY_TYPE:  Do we send every mail type to every user only once before 
                     we blacklist them for it?
 RSYNC_MIRROR:  Which rsync server to sync packages from
 DEFAULT_LOCALE: Default locale
 SUPP_LANGS:    Supported languages by GetTor
 PACKAGES:      List of packages GetTor serves

 If no valid config file is provided to __init__, gettorConf will try to use
 '~/.gettor.conf' as default config file. If that fails, the default values from
 CONFIG_DEFAULTS will be used.

'''

import os

__all__ = ["Config"]

CONFIG_DEFAULTS = {
   'MAIL_FROM': "GetTor <gettor@torproject.org>",
   'BASEDIR':  "/tmp",
   'DELAY_ALERT': True,
   'LOGFILE': "gettorlog",
   'LOGLEVEL': "DEBUG",
   'PASSFILE': "gettor.pass",
   'DUMPFILE': "./gettor.dump",
   'BLACKLIST_BY_TYPE': True,
   'RSYNC_MIRROR': "rsync.torproject.org",
   'DEFAULT_LOCALE': "en",
   'SUPP_LANGS': { 'en': ("english", ), },
   'PACKAGES': { 
       "tor-browser-bundle": 
           ("tor-browser-.*_en-US.exe$", 
            "tor-browser-.*_en-US_split"), }
}

class Config:
    '''
    Initialize gettor with default values if one or more values are missing 
    from the config file. This will return entirely default values if the 
    configuration file is missing. Our default file location is ~/.gettor.conf
    of $USER.
    '''

    def __init__(self, path = os.path.expanduser("~/.gettor.conf")):
       """Most of the work happens here. Parse config, merge with default 
          values, prepare outConf.
       """

       self.useConf = {}
       configFile = os.path.expanduser(path)
       execfile(configFile, self.useConf)
       self.__dict__.update(self.useConf)
       self.setMissing()

    def setMissing(self):
       for k,v in CONFIG_DEFAULTS.items():
          if not hasattr(self, k):
             setattr(self,k,v)
