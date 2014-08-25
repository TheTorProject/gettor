# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser Bundle distribution system.
#
# :authors: Israel Leiva <ilv@riseup.net>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2014, The Tor Project, Inc.
#               (c) 2014, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

import os
import re
import sys
import time
import gettext
import hashlib
import logging
import ConfigParser

from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout

import core
import utils
import blacklist


"""XMPP module for processing requests."""


class Bot(ClientXMPP):
    """XMPP bot.

    Handle messages and pass them to XMPP module for parsing.

    """

    def __init__(self, jid, password, xmpp_obj):
        ClientXMPP.__init__(self, jid, password)

        self.xmpp = xmpp_obj
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

    def session_start(self, event):
        self.send_presence()
        self.get_roster()

        try:
            self.get_roster()
        except IqError as err:
            logging.error('There was an error getting the roster')
            logging.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logging.error('Server is taking too long to respond')
            self.disconnect()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            msg_to_send = self.xmpp.parse_request(msg['from'], msg['body'])
            if msg_to_send:
                msg.reply(msg_to_send).send()


class ConfigurationError(Exception):
    pass


class InternalError(Exception):
    pass


class XMPP(object):
    """Receive and reply requests by XMPP.

    Public methods:

        parse_request(): parses a message and tries to figure out what the user
                         is asking for.

    Exceptions:

        ConfigurationError: Bad configuration.
        InternalError: Something went wrong internally.

    """

    def __init__(self, cfg=None):
    	"""Create new object by reading a configuration file.

        :param: cfg (string) the path of the configuration file.

        """
        # define a set of default values
        DEFAULT_CONFIG_FILE = 'xmpp.cfg'

        logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")
        log = logging.getLogger(__name__)
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = DEFAULT_CONFIG_FILE
            log.info("Using default configuration")

        log.info("Reading configuration file %s" % cfg)
        config.read(cfg)

        try:
            self.user = config.get('account', 'user')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'user' from 'account' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.password = config.get('account', 'password')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'password' from 'account' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.basedir = config.get('general', 'basedir')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'basedir' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.core_cfg = config.get('general', 'core_cfg')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'core_cfg' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            blacklist_cfg = config.get('blacklist', 'cfg')
            self.bl = blacklist_cfg
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'cfg' from 'blacklist' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.bl_max_req = config.get('blacklist', 'max_requests')
            self.bl_max_req = int(self.bl_max_req)
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'max_requests' from 'blacklist' (%s)"
                        % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.bl_wait_time = config.get('blacklist', 'wait_time')
            self.bl_wait_time = int(self.bl_wait_time)
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'wait_time' from 'blacklist' (%s)"
                        % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.i18ndir = config.get('i18n', 'dir')
            self.i18ndir = os.path.join(self.basedir, self.i18ndir)
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'dir' from 'i18n' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.logdir = config.get('log', 'dir')
            self.logdir = os.path.join(self.basedir, self.logdir)
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'dir' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.logdir_msgs = config.get('log', 'msgs_dir')
            self.logdir_msgs = os.path.join(self.logdir, self.logdir_msgs)
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'msgs_dir' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.loglevel = config.get('log', 'level')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'level' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        # keep log levels separated
        self.log = utils.filter_logging(log, self.logdir, self.loglevel)
        self.log.setLevel(logging.getLevelName(self.loglevel))
        log.debug('Redirecting logging to %s' % self.logdir)

        # stop logging on stdout from now on
        log.propagate = False
        self.log.debug("New xmpp object created")

    def start_bot(self):
        """Start the bot for handling requests.

        Start a new sleekxmpp bot.

        """

        self.log.debug("Calling sleekmppp bot")
        xmpp = Bot(self.user, self.password, self)
        xmpp.connect()
        xmpp.process(block=True)

    def _is_blacklisted(self, account):
        """Check if a user is blacklisted.

        :param: addr (string) the hashed address of the user.

        :return: true is the address is blacklisted, false otherwise.

        """
        anon_acc = utils.get_sha256(account)
        bl = blacklist.Blacklist(self.bl)
        self.log.debug("Checking if address %s is blacklisted" % anon_acc)

        try:
            bl.is_blacklisted(anon_acc, 'XMPP', self.bl_max_req,
                              self.bl_wait_time)
            return False
        except blacklist.BlacklistError as e:
            self.log.info("Blacklisted address %s. Reason: %s" % (anon_acc, e))
            return True

    def _get_msg(self, msgid, lc):
        """Get message identified by msgid in a specific locale.

        :param: msgid (string) the identifier of a string.
        :param: lc (string) the locale.

        :return: (string) the message from the .po file.

        """
        self.log.debug("Getting message '%s' for locale %s" % (msgid, lc))
        # obtain the content in the proper language
        t = gettext.translation(lc, self.i18ndir, languages=[lc])
        _ = t.ugettext

        msgstr = _(msgid)
        return msgstr

    def _parse_text(self, msg, core_obj):
        """Parse the text part of a message.

        Split the message in words and look for patterns for locale,
        operating system and built-in pluggable transport info.

        :param: msg (string) the message received.
        :param: core_obj (object) the object of gettor core module.

        :return: request (list) 4-tuple with locale, os, type of request
                 and pt info.

        """
        self.log.debug("Starting text parsing")
        # core knows what OS are supported
        supported_os = core_obj.get_supported_os()
        supported_lc = core_obj.get_supported_lc()

        # default values
        req = {}
        req['lc'] = 'en'
        req['os'] = ''
        req['type'] = 'help'
        req['pt'] = False
        found_lc = False
        found_os = False
        found_help = False

        # analyze every word
        # request shouldn't be more than 10 words long, so there should
        # be a limit for the amount of words
        for word in msg.split(' '):
            # check for help request
            if not found_os and re.match('help', word, re.IGNORECASE):
                self.log.info("Request for help found")
                req['type'] = 'help'
                found_help = True
            # look for locale, os and pt
            if not found_lc:
                for lc in supported_lc:
                    if re.match(lc, word, re.IGNORECASE):
                        found_lc = True
                        req['lc'] = lc
                        self.log.debug("Found locale: %s" % lc)
            if not found_os and not found_help:
                for os in supported_os:
                    if re.match(os, word, re.IGNORECASE):
                        found_os = True
                        req['os'] = os
                        req['type'] = 'links'
                        self.log.debug("Found OS: %s" % os)
            if re.match("obfs|plugabble|transport|pt", word, re.IGNORECASE):
                req['pt'] = True
                self.log.debug("Found PT request")

        return req

    def parse_request(self, account, msg):
        """Process the request received.

        Check if the user is not blacklisted and then check the body of
        the message to find out what is asking.

        :param: account (string) the account that did the request.
        :param: msg (string) the body of the message sent to us.

        :return: (string/None) the message to be sent to the user via the
                 bot, or None if the user is blacklisted.

        """
        bogus_request = False
        reply = ''
        logfile = ''
        status = ''
        req = None
        core_obj = core.Core(self.core_cfg)

        try:
            if self._is_blacklisted(str(account)):
                status = 'blacklisted'
                bogus_request = True

            if not bogus_request:
                self.log.debug("Request seems legit, let's parse it")
                # let's try to guess what the user is asking
                req = self._parse_text(str(msg), core_obj)

                if req['type'] == 'help':
                    status = 'success'
                    self.log.debug("Got a help request")
                    reply = self._get_msg('help', req['lc'])
                elif req['type'] == 'links':
                    self.log.debug("Got a links request")
                    try:
                        links = core_obj.get_links("XMPP", req['os'],
                                                   req['lc'])
                        # did the user asked for PT stuff?
                        if req['pt']:
                            self.log.debug("Also asked for PT info")
                            reply = self._get_msg('links_pt', req['lc'])
                            reply = reply % (req['os'], req['lc'], links)
                        else:
                            reply = self._get_msg('links', req['lc'])
                            reply = reply % (req['os'], req['lc'], links)

                        status = 'success'
                    except (core.ConfigurationError, core.InternalError) as e:
                        # if core failes, send the user an error message, but
                        # keep going
                        status = 'core_error'
                        self.log.debug("Something went wrong with Core")
                        reply = self._get_msg('internal_error', req['lc'])

                    # if the user asked for an unsupported locale, warn him
                    # and keep going
                    except core.UnsupportedLocaleError as e:
                        status = 'unsupported_lc'
                        self.log.debug("User asked for unsupported locale")
                        reply = self._get_msg('unsupported_lc', req['lc'])
        finally:
            # keep stats
            self.log.debug("Request processed, saving stats.")

            if req:
                core_obj.add_request_to_db('XMPP',
                                           req['type'], req['os'],
                                           req['lc'], req['pt'],
                                           status, logfile)
            else:
                # invalid request, so no info about it
                # logfiles were created for this
                core_obj.add_request_to_db('XMPP', '', '', '', '',
                                           status, logfile)

            return reply
