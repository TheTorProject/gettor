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


class ConfigError(Exception):
    pass


class InternalError(Exception):
    pass


class Blacklist(object):
    """Manage blacklisting of users.

    Public methods:

        is_blacklisted(): Check if someone is blacklisted.

    Exceptions:

         ConfigurationError: Bad configuration.
         BlacklistError: User is blacklisted.
         InternalError: Something went wrong internally.

    """

    def __init__(self, cfg=None):
    	"""Create new object by reading a configuration file.

        :param: cfg (string) path of the configuration file.

        """
        default_cfg = 'blacklist.cfg'
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = default_cfg

        try:
            with open(cfg) as f:
                config.readfp(f)
        except IOError:
            raise ConfigError("File %s not found!" % cfg)

        try:
            dbname = config.get('general', 'db')
            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'blacklist.log')
            loglevel = config.get('log', 'level')
            self.db = db.DB(dbname)

        except ConfigParser.Error as e:
            raise ConfigError("%s" % e)
        except db.Exception as e:
            raise ConfigError("%s" % e)

        # logging
        log = logging.getLogger(__name__)

        logging_format = utils.get_logging_format()
        date_format = utils.get_date_format()
        formatter = logging.Formatter(logging_format, date_format)

        log.info('Redirecting BLACKLIST logging to %s' % logfile)
        logfileh = logging.FileHandler(logfile, mode='a+')
        logfileh.setFormatter(formatter)
        logfileh.setLevel(logging.getLevelName(loglevel))
        log.addHandler(logfileh)

        # stop logging on stdout from now on
        log.propagate = False
        self.log = log

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
        try:
            self.log.info("Trying to get info from user")
            self.db.connect()
            r = self.db.get_user(user, service)
            if r:
                # permanently blacklisted
                if r['blocked']:
                    self.log.warning("Request from user permanently blocked")
                    self.db.update_user(user, service, r['times']+1, 1)
                    raise BlacklistError("Blocked user")
                # don't be greedy
                elif r['times'] >= max_req:
                    last = datetime.datetime.fromtimestamp(
                        float(r['last_request'])
                    )
                    next = last + datetime.timedelta(minutes=wait_time)

                    if datetime.datetime.now() < next:
                        self.log.warning("Too many requests from same user")
                        self.db.update_user(user, service, r['times']+1, 0)
                        raise BlacklistError("Too many requests")
                    else:
                        # fresh user again!
                        self.log.info("Updating counter for existing user")
                        self.db.update_user(user, service, 1, 0)
                else:
                    # adding up a request for user
                    self.log.info("Request from existing user")
                    self.db.update_user(user, service, r['times']+1, 0)
            else:
                # new request for user
                self.log.info("Request from new user")
                self.db.add_user(user, service, 0)
        except db.DBError as e:
            self.log.error("Something failed!")
            raise InternalError("Error with database (%s)" % str(e))
        except BlacklistError as e:
            raise BlacklistError(e)
