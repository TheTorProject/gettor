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
            # error getting the roster
            # logging.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            # server is taking too long to respond
            self.disconnect()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            msg_to_send = self.xmpp.parse_request(msg['from'], msg['body'])
            if msg_to_send:
                msg.reply(msg_to_send).send()


class ConfigError(Exception):
    pass


class InternalError(Exception):
    pass


class XMPP(object):
    """Receive and reply requests by XMPP.

    Public methods:

        parse_request(): parses a message and tries to figure out what the user
                         is asking for.

    Exceptions:

        ConfigError: Bad configuration.
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

        config.read(cfg)

        try:
            self.user = config.get('account', 'user')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'user' from 'account'")

        try:
            self.password = config.get('account', 'password')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'password' from 'account'")

        try:
            self.core_cfg = config.get('general', 'core_cfg')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'core_cfg' from 'general'")

        try:
            blacklist_cfg = config.get('blacklist', 'cfg')
            self.bl = blacklist_cfg
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'cfg' from 'blacklist'")

        try:
            self.bl_max_req = config.get('blacklist', 'max_requests')
            self.bl_max_req = int(self.bl_max_req)
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'max_requests' from 'blacklist'")

        try:
            self.bl_wait_time = config.get('blacklist', 'wait_time')
            self.bl_wait_time = int(self.bl_wait_time)
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'wait_time' from 'blacklist'")

        try:
            self.i18ndir = config.get('i18n', 'dir')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'dir' from 'i18n'")

        try:
            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'xmpp.log')
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

    def start_bot(self):
        """Start the bot for handling requests.

        Start a new sleekxmpp bot.

        """
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

        try:
            bl.is_blacklisted(anon_acc, 'XMPP', self.bl_max_req,
                              self.bl_wait_time)
            return False
        except blacklist.BlacklistError as e:
            return True

    def _get_msg(self, msgid, lc):
        """Get message identified by msgid in a specific locale.

        :param: msgid (string) the identifier of a string.
        :param: lc (string) the locale.

        :return: (string) the message from the .po file.

        """
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
        # core knows what OS are supported
        supported_os = core_obj.get_supported_os()
        supported_lc = core_obj.get_supported_lc()

        # default values
        req = {}
        req['lc'] = 'en'
        req['os'] = None
        req['type'] = 'help'
        found_lc = False
        found_os = False

        # analyze every word
        # request shouldn't be more than 10 words long, so there should
        # be a limit for the amount of words
        for word in msg.split(' '):
            # look for lc and os
            if not found_lc:
                for lc in supported_lc:
                    if re.match(lc, word, re.IGNORECASE):
                        found_lc = True
                        req['lc'] = lc
            if not found_os:
                for os in supported_os:
                    if re.match(os, word, re.IGNORECASE):
                        found_os = True
                        req['os'] = os
                        req['type'] = 'links'
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
        status = ''
        req = None
        core_obj = core.Core(self.core_cfg)

        try:
            if self._is_blacklisted(str(account)):
                status = 'blacklisted'
                bogus_request = True

            if not bogus_request:
                # let's try to guess what the user is asking
                req = self._parse_text(str(msg), core_obj)

                if req['type'] == 'help':
                    status = 'success'
                    reply = self._get_msg('help', req['lc'])
                elif req['type'] == 'links':
                    try:
                        links = core_obj.get_links("XMPP", req['os'],
                                                   req['lc'])
                        reply = self._get_msg('links', req['lc'])
                        reply = reply % (req['os'], req['lc'], links)

                        status = 'success'
                    except (core.ConfigError, core.InternalError) as e:
                        # if core failes, send the user an error message, but
                        # keep going
                        status = 'core_error'
                        reply = self._get_msg('internal_error', req['lc'])
        finally:
            # keep stats
            if req:
                core_obj.add_request_to_db()

            return reply
