# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser Bundle distribution system.
#

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

import utils
import core


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


class BlacklistError(Exception):
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
        BlacklistError: User is blacklisted.
        InternalError: Something went wrong internally.

    """

    def __init__(self, cfg=None):
    	"""Create new object by reading a configuration file.

        Params: cfg - path of the configuration file.

        """
        # Define a set of default values
        DEFAULT_CONFIG_FILE = 'xmpp.cfg'

        logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")
        logger = logging.getLogger(__name__)
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = DEFAULT_CONFIG_FILE
            logger.info("Using default configuration")

        logger.info("Reading configuration file %s" % cfg)
        config.read(cfg)

        try:
            self.user = config.get('account', 'user')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'user' from 'account' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.password = config.get('account', 'password')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'password' from 'account' (%s)" %
                           cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.basedir = config.get('general', 'basedir')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'basedir' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.logdir = config.get('log', 'dir')
            self.logdir = os.path.join(self.basedir, self.logdir)
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'dir' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.logdir_msgs = config.get('log', 'msgs_dir')
            self.logdir_msgs = os.path.join(self.logdir, self.logdir_msgs)
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'msgs_dir' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.loglevel = config.get('log', 'level')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'level' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        # Use default values
        self.core = core.Core()

        # Keep log levels separated
        self.logger = utils.filter_logging(logger, self.logdir, self.loglevel)
        self.logger.setLevel(logging.getLevelName(self.loglevel))
        logger.debug('Redirecting logging to %s' % self.logdir)

        # Stop logging on stdout from now on
        logger.propagate = False
        self.logger.debug("New xmpp object created")

    def start_bot(self):
        """Start the bot for handling requests.

        Start a new sleekxmpp bot.

        """

        self.logger.debug("Calling sleekmppp bot")
        xmpp = Bot(self.user, self.password, self)
        xmpp.connect()
        xmpp.process(block=True)

    def _get_sha1(self, string):
        """Get sha1 of a string.

        Used whenever we want to do things with accounts (log, blacklist,
        etc.)

        Params: The string to be sha1'ed.

        Returns: sha1 of string.

        """
        return str(hashlib.sha1(string).hexdigest())

    def _check_blacklist(self, account):
        """Check if an account is blacklisted.

        Look for the account in the file of blacklisted accounts.

        Raises: BlacklistError if the user is blacklisted.

        Params: account - the account we want to check.

        """
        anon_account = self._get_sha1(account)
        self.logger.debug("Checking if address %s is blacklisted" %
                          anon_account)

        # if blacklisted:
        #    raise BlacklistError("Account %s is blacklisted!" % anon_account)

    def _get_help_msg(self, locale):
        """Get help message for a given locale.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and return the message.

        Return: a string containing the message.

        """
        self.logger.debug("Getting help message")
        # Obtain the content in the proper language
        t = gettext.translation(locale, './xmpp/i18n', languages=[locale])
        _ = t.ugettext

        help_msg = _('help_msg')
        return help_msg

    def _get_unsupported_locale_msg(self, locale):
        """Get unsupported locale message for a given locale.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and return the message.

        Return: a string containing the message.

        """
        self.logger.debug("Getting unsupported locale message")
        # Obtain the content in the proper language
        t = gettext.translation(locale, './xmpp/i18n', languages=[locale])
        _ = t.ugettext

        unsupported_locale_msg = _('unsupported_locale_msg')
        return unsupported_locale_msg

    def _get_unsupported_os_msg(self, locale):
        """Get unsupported OS message for a given locale.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and return the message.

        Return: a string containing the message.

        """
        self.logger.debug("Getting unsupported os message")
        # Obtain the content in the proper language
        t = gettext.translation(locale, './xmpp/i18n', languages=[locale])
        _ = t.ugettext

        unsupported_os_msg = _('unsupported_os_msg')
        return unsupported_os_msg

    def _get_internal_error_msg(self, locale):
        """Get internal error message for a given locale.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and return the message.

        Return: a string containing the message.

        """
        self.logger.debug("Getting internal error message")
        # Obtain the content in the proper language
        t = gettext.translation(locale, './xmpp/i18n', languages=[locale])
        _ = t.ugettext

        internal_error_msg = _('internal_error_msg')
        return internal_error_msg

    def _get_links_msg(self, locale, operating_system, pt, links):
        """Get links message for a given locale, operating system and PT
        request.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and return the message.

        Return: a string containing the message.
        """
        self.logger.debug("Getting links message")
        # Obtain the content in the proper language
        t = gettext.translation(locale, './xmpp/i18n', languages=[locale])
        _ = t.ugettext

        if pt:
            links_msg = _('links_pt_msg')
        else:
            links_msg = _('links_msg')

        links_msg = links_msg % links

        return links_msg

    def _parse_text(self, msg):
        """Parse the text part of a message.

        Split the message in words and look for patterns for locale,
        operating system and built-in pluggable transport info.

        """
        self.logger.debug("Starting text parsing")
        # core knows what OS are supported
        supported_os = self.core.get_supported_os()
        supported_locales = self.core.get_supported_locales()

        # default values
        request = {}
        request['locale'] = 'en'
        request['os'] = 'windows'
        request['type'] = 'help'
        request['pt'] = False
        found_locale = False
        found_os = False

        # analyze every word
        # request shouldn't be more than 10 words long, so there should
        # be a limit for the amount of words
        for word in msg.split(' '):
            # look for locale, os and pt
            if not found_locale:
                for locale in supported_locales:
                    if re.match(locale, word, re.IGNORECASE):
                        found_locale = True
                        request['locale'] = locale
                        self.logger.debug("Found locale: %s" % locale)
            if not found_os:
                for operating_system in supported_os:
                    if re.match(operating_system, word, re.IGNORECASE):
                        found_os = True
                        request['os'] = operating_system
                        request['type'] = 'links'
                        self.logger.debug("Found OS: %s" % operating_system)
            if re.match("obfs|plugabble transport|pt", word,
                        re.IGNORECASE):
                request['pt'] = True
                self.logger.debug("Found PT request")

        return request

    def parse_request(self, account, msg):
        """Process the request received.

        Check if the user is not blacklisted and then check the body of
        the message to find out what is asking.

        Params: account - the account that did the request.
                msg - the body of the message sent to us.

        """
        try:
            self._check_blacklist(str(account))
        except BlacklistError as e:
            return None

        # let's try to guess what the user is asking
        request = self._parse_text(str(msg))

        if request['type'] == 'help':
            return_msg = self._get_help_msg(request['locale'])
        elif request['type'] == 'links':
            try:
                links = self.core.get_links("XMPP", request['os'],
                                            request['locale'])

                return_msg = self._get_links_msg(request['locale'], 
                                                 request['os'], request['pt'],
                                                 links)

            except (core.ConfigurationError, core.InternalError) as e:
                return_msg = self._get_internal_error_msg(request['locale'])

            except core.UnsupportedLocaleError as e:
                self.core._get_unsupported_locale_msg(request['locale'])

            except core.UnsupportedOSError as e:
                self.core._get_unsupported_os_msg(request['locale'])

        return return_msg
