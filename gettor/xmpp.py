# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: Israel Leiva <ilv@riseup.net>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2015, The Tor Project, Inc.
#               (c) 2015, Israel Leiva
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
from sleekxmpp.xmlstream.stanzabase import JID
from sleekxmpp.exceptions import IqError, IqTimeout

import core
import utils
import blacklist


"""XMPP module for processing requests."""


class ConfigError(Exception):
    pass


class InternalError(Exception):
    pass


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
            self.xmpp.log.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            # server is taking too long to respond
            self.xmpp.log.error("Server is taking too long to respond")
            self.disconnect()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            msg_to_send = self.xmpp.parse_request(msg['from'], msg['body'])
            if msg_to_send:
                msg.reply(msg_to_send).send()


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
        default_cfg = 'xmpp.cfg'
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = default_cfg

        try:
            with open(cfg) as f:
                config.readfp(f)
        except IOError:
            raise ConfigError("File %s not found!" % cfg)

        try:
            self.user = config.get('account', 'user')
            self.password = config.get('account', 'password')

            self.mirrors = config.get('general', 'mirrors')
            self.max_words = config.get('general', 'max_words')
            self.max_words = int(self.max_words)
            core_cfg = config.get('general', 'core_cfg')
            self.core = core.Core(core_cfg)
            self.i18ndir = config.get('i18n', 'dir')

            blacklist_cfg = config.get('blacklist', 'cfg')
            self.bl = blacklist.Blacklist(blacklist_cfg)
            self.bl_max_req = config.get('blacklist', 'max_requests')
            self.bl_max_req = int(self.bl_max_req)
            self.bl_wait_time = config.get('blacklist', 'wait_time')
            self.bl_wait_time = int(self.bl_wait_time)

            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'xmpp.log')
            loglevel = config.get('log', 'level')

        except ConfigParser.Error as e:
            raise ConfigError("Configuration error: %s" % str(e))
        except blacklist.ConfigError as e:
            raise InternalError("Blacklist error: %s" % str(e))
        except core.ConfigError as e:
            raise InternalError("Core error: %s" % str(e))

        # logging
        log = logging.getLogger(__name__)

        logging_format = utils.get_logging_format()
        date_format = utils.get_date_format()
        formatter = logging.Formatter(logging_format, date_format)

        log.info('Redirecting XMPP logging to %s' % logfile)
        logfileh = logging.FileHandler(logfile, mode='a+')
        logfileh.setFormatter(formatter)
        logfileh.setLevel(logging.getLevelName(loglevel))
        log.addHandler(logfileh)

        # stop logging on stdout from now on
        log.propagate = False
        self.log = log

    def start_bot(self):
        """Start the bot for handling requests.

        Start a new sleekxmpp bot.

        """
        self.log.info("Starting the bot with account %s" % self.user)
        xmpp = Bot(self.user, self.password, self)
        xmpp.connect()
        xmpp.process(block=True)

    def _is_blacklisted(self, account):
        """Check if a user is blacklisted.

        :param: addr (string) the hashed address of the user.

        :return: true is the address is blacklisted, false otherwise.

        """
        anon_acc = utils.get_sha256(account)

        try:
            self.bl.is_blacklisted(
                anon_acc, 'XMPP', self.bl_max_req, self.bl_wait_time
            )
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
        self.log.debug("Trying to get translated text")
        try:
            t = gettext.translation(lc, self.i18ndir, languages=[lc])
            _ = t.ugettext

            msgstr = _(msgid)
            return msgstr
        except IOError as e:
            raise ConfigError("%s" % str(e))

    def _parse_text(self, msg):
        """Parse the text part of a message.

        Split the message in words and look for patterns for locale,
        operating system and built-in pluggable transport info.

        :param: msg (string) the message received.
        :param: core_obj (object) the object of gettor core module.

        :return: request (list) 4-tuple with locale, os, type of request
                 and pt info.

        """
        # core knows what OS are supported
        supported_os = self.core.get_supported_os()
        supported_lc = self.core.get_supported_lc()

        self.log.debug("Parsing text")
        # default values
        req = {}
        req['lc'] = 'en'
        req['os'] = None
        req['type'] = 'help'

        found_lc = False
        found_os = False
        found_mirrors = False

        # analyze every word
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
            # mirrors
            if not found_mirrors:
                if re.match("mirrors?", word, re.IGNORECASE):
                    found_mirrors = True
                    req['type'] = 'mirrors'
            if (found_lc and found_os) or (found_lc and found_mirrors):
                break

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

        self.log.debug("Parsing request")
        try:
            if self._is_blacklisted(str(account)):
                self.log.info('blacklist; none; none')
                bogus_request = True

            # first let's find out how many words are in the message
            # request shouldn't be longer than 3 words, but just in case
            words = re.split('\s+', msg.strip())
            if len(words) > self.max_words:
                bogus_request = True
                self.log.info("Message way too long")
                self.log.info('invalid; none; none')
                reply = self._get_msg('message_error', 'en')

            if not bogus_request:
                self.log.debug("Request seems legit, let's parse it")
                # let's try to guess what the user is asking
                req = self._parse_text(str(msg))

                if req['type'] == 'help':
                    self.log.info('help; none; %s' % req['lc'])
                    reply = self._get_msg('help', 'en')

                elif req['type'] == 'mirrors':
                    self.log.info('mirrors; none; %s' % req['lc'])
                    reply = self._get_msg('mirrors', 'en')
                    try:
                        with open(self.mirrors, "r") as list_mirrors:
                            mirrors = list_mirrors.read()
                        reply = reply % mirrors
                    except IOError as e:
                        reply = self._get_msg('mirrors_unavailable', 'en')

                elif req['type'] == 'links':
                    self.log.info('links; %s; %s' % (req['os'], req['lc']))
                    links = self.core.get_links(
                        "XMPP",
                        req['os'],
                        req['lc']
                    )
                    reply = self._get_msg('links', 'en')
                    reply = reply % (req['os'], req['lc'], links)

        except (core.ConfigError, core.InternalError) as e:
            # if core failes, send the user an error message, but keep going
            self.log.error("Something went wrong internally: %s" % str(e))
            reply = self._get_msg('internal_error', req['lc'])

        finally:
            return reply
