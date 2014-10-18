# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: Israel Leiva <ilv@riseup.net>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2014, The Tor Project, Inc.
#               (c) 2014, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

import os
import time
import logging
import sqlite3
import datetime
import ConfigParser

import db
import utils

"""Blacklist module for managing blacklisting of users."""


class BlacklistError(Exception):
    pass


class Blacklist(object):
    """Manage blacklisting of users.

    Public methods:

        is_blacklisted(): Check if someone is blacklisted.

    Exceptions:

         ConfigurationError: Bad configuration.
         BlacklistError: User is blacklisted.

    """

    def __init__(self, cfg=None):
    	"""Create new object by reading a configuration file.

        :param: cfg (string) path of the configuration file.

        """
        # define a set of default values
        DEFAULT_CONFIG_FILE = 'blacklist.cfg'

        logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")
        log = logging.getLogger(__name__)
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = DEFAULT_CONFIG_FILE

        config.read(cfg)

        try:
            dbname = config.get('general', 'db')
            self.db = db.DB(dbname)
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'db' from 'general'")

        try:
            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'blacklist.log')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'dir' from 'log'")

        try:
            loglevel = config.get('log', 'level')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'level' from 'log'")

        # establish log level and redirect to log file
        log.info('Redirecting logging to %s' % logfile)
        logfileh = logging.FileHandler(logfile, mode='a+')
        logfileh.setLevel(logging.getLevelName(loglevel))
        log.addHandler(logfileh)

        # stop logging on stdout from now on
        log.propagate = False

    def is_blacklisted(self, user, service, max_req, wait_time):
        """Check if a user is blacklisted.

        The user is blacklisted if:

        a) The 'blocked' field is set to one, meaning that is permanently
        blacklisted.

        b) Does too many requests on a short period of time. For now, a user
        that makes more than 'max_req' requests should wait 'wait_time'
        minutes to make a new request.

        :param: user (string) the hashed user.
        :param: service (string) the service the user is making a request to.
        :param: max_req (int) maximum number of requests a user can make
                in a row.
        :param: wait_time (int) amount of time the user must wait before
                making requests again after 'max_req' requests is reached.
                For now this is considered in minutes.

        :raise: BlacklistError if the user is blacklisted

        """
        r = self.db.get_user(user, service)
        if r:
            # permanently blacklisted
            if r['blocked']:
                self.db.update_user(user, service, r['times']+1, 1)
                raise BlacklistError("Blocked user")
            # don't be greedy
            elif r['times'] >= max_req:
                last = datetime.datetime.fromtimestamp(float(
                                                       r['last_request']))
                next = last + datetime.timedelta(minutes=wait_time)

                if datetime.datetime.now() < next:
                    # too many requests from the same user
                    self.db.update_user(user, service, r['times']+1, 0)
                    raise BlacklistError("Too many requests")
                else:
                    # fresh user again!
                    self.db.update_user(user, service, 1, 0)
            else:
                # adding up a request for user
                self.db.update_user(user, service, r['times']+1, 0)
        else:
            # new request for user
            self.db.add_user(user, service, 0)
