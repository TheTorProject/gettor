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
import potr
import time
import gettext
import hashlib
import logging
import potr.crypt
import ConfigParser

from base64 import b64encode, b64decode
from potr.compatcrypto import generateDefaultKey

from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream.stanzabase import JID
from sleekxmpp.exceptions import IqError, IqTimeout

import core
import utils
import blacklist


"""XMPP module for processing requests."""


DEFAULT_POLICY_FLAGS = {
  'ALLOW_V1': False,
  'ALLOW_V2': True,
  'REQUIRE_ENCRYPTION': False,
}


PROTOCOL='xmpp'
MMS=1024


class ConfigError(Exception):
    pass


class InternalError(Exception):
    pass


class OTRContext(potr.context.Context):
    def __init__(self, account, client, peer):
        super(OTRContext, self).__init__(account, peer)
        self.account = account
        self.client = client
        self.peer = peer

    # This method has should return True or False for a variety of policies.
    # to start off, 'ALLOW_V1', 'ALLOW_V2', and 'REQUIRE_ENCRYPTION' seemed 
    # like the minimum
    def getPolicy(self, key):
        if key in DEFAULT_POLICY_FLAGS:
            return DEFAULT_POLICY_FLAGS[key]
        else:
            return False

    def inject(self, msg, appdata=None):
        msg_to_send = self.xmpp.parse_request(
            msg['from'],
            msg['body']
        )

        self.client.send_message(
            mto=self.peer,
            mbody=msg_to_send,
        )
        # This method is called when potr needs to inject a message into the
        # stream. For instance, upon receiving an initiating stanza, potr 
        # will inject the key exchange messages here is where you should hook
        # into your app and actually send the message potr gives you

    def setState(self, newstate):
        # Overriding this method is not strictly necessary, but this is a 
        # good place to hook state changes for notifying your app, to give 
        # your user feedback. I used this method to set icon state and insert 
        # a message into chat history, notifying the user that encryption is 
        # or is not enabled. Don't forget to call the base class method
        super(OTRContext, self).setState(newstate)


class OTRAccount(potr.context.Account):

    def __init__(self, jid, pk=None):
        global PROTOCOL, MMS
        super(OTRAccount, self).__init__(jid, PROTOCOL, MMS)
        #self.keyFilePath = os.path.join("./otr-test", jid)

        if pk is None:
            pkb64 = b64encode(generateDefaultKey().serializePrivateKey())
            msg = 'A base64-encoded DSA OTR private key for the XMPP' \
                  'account is required. Here is a fresh one you can use: \n'
            raise ValueError(msg + pkb64)
        else:
            self.pk = potr.crypt.PK.parsePrivateKey(b64decode(pk))[0]

    def loadPrivkey(self):
        return self.pk

    def savePrivkey(self):
        pass


class OTRContextManager:
    # The jid parameter is the logged in user's jid.  I use it to instantiate 
    # an object of the *potr.context.Account* subclass described earlier.
    def __init__(self, account):
        self.account = account
        self.contexts = {}

    # This method starts a context with a peer if none exists, or returns it 
    # otherwise
    def start_context(self, client, other):
        if not other in self.contexts:
            self.contexts[other] = OTRContext(self.account, client, other)
        return self.contexts[other]

    # just an alias for start_context
    def get_context_for_user(self, client, other):
        return self.start_context(client, other)


class Bot(ClientXMPP):
    """XMPP bot.

    Handle messages and pass them to XMPP module for parsing.

    """

    def __init__(self, jid, password, xmpp_obj):
        ClientXMPP.__init__(self, jid, password)

        self.xmpp = xmpp_obj
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

        self.otr_account = OTRAccount(jid, self.xmpp.pk)
        self.otr_manager = OTRContextManager(self.otr_account)

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
        otrctx = self.otr_manager.get_context_for_user(self, str(msg['from']))

        self.xmpp.log.info("New message received")
        encrypted = True
        try:
            # Attempt to pass the msg via *potr.context.Context.receiveMessage*
            # there are a couple of possible cases
            res = otrctx.receiveMessage(msg["body"])
        except potr.context.UnencryptedMessage, message:
            # potr raises an UnencryptedMessage exception when a message is
            # unencrypted but the context is encrypted this indicates a
            # plaintext message came through a supposedly encrypted channel
            # it is appropriate here to warn your user!
            encrypted = False
        except potr.context.NotEncryptedError:
            # potr auto-responds saying we didn't expect an encrypted message
            return

        if encrypted == False:
            self.xmpp.log.debug("Unencrypted message received. Replying...")
            if msg['type'] in ('chat', 'normal'):
                # Here is where you handle plain text messages
                msg_to_send = self.xmpp.parse_request(
                    msg['from'],
                    msg['body']
                )
                msg.reply(msg_to_send).send()
        else:
            self.xmpp.log.debug("Encrypted message received. Replying...")
            if res[0] != None:
                # Here is where you handle decrypted messages. receiveMessage()
                # will return a tuple, the first part of which will be the
                # decrypted message
                otrctx = self.otr_manager.get_context_for_user(
                    self,
                    str(msg['from'])
                )
                if otrctx.state == potr.context.STATE_ENCRYPTED:
                    self.xmpp.log.debug("Encrypting...")
                    # The context state should currently be encrypted, so
                    # encrypt outgoing message passing the plain text message
                    # into Context.sendMessage will trigger Context.inject with
                    # an encrypted message.
                    msg_to_send = self.xmpp.parse_request(
                        msg['from'],
                        msg['body']
                    )
                    otrctx.sendMessage(0, msg_to_send)
                else:
                    # The outgoing state is not encrypted, so send it plain
                    # text, if that is supported in your app
                    self.xmpp.log.debug("Sending unencrypted message...")
                    msg_to_send = self.xmpp.parse_request(
                        msg['from'],
                        msg['body']
                    )
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
            self.pk = config.get('account', 'pk')

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
                self.log.info("Request from blacklisted account!")
                status = 'blacklisted'
                bogus_request = True

            # first let's find out how many words are in the message
            # request shouldn't be longer than 3 words, but just in case
            words = msg.split(' ')
            if len(words) > self.max_words:
                bogus_request = True
                self.log.info("Message way too long")
                status = 'error'
                reply = self._get_msg('message_error', 'en')

            if not bogus_request:
                self.log.debug("Request seems legit, let's parse it")
                # let's try to guess what the user is asking
                req = self._parse_text(str(msg))

                if req['type'] == 'help':
                    self.log.debug("Type of request: help")
                    status = 'success'
                    reply = self._get_msg('help', 'en')

                elif req['type'] == 'mirrors':
                    self.log.debug("Type of request: mirrors")
                    status = 'success'
                    reply = self._get_msg('mirrors', 'en')
                    try:
                        with open(self.mirrors, "r") as list_mirrors:
                            mirrors = list_mirrors.read()
                        reply = reply % mirrors
                    except IOError as e:
                        reply = self._get_msg('mirrors_unavailable', 'en')

                elif req['type'] == 'links':
                    self.log.debug("Type of request: help")
                    links = self.core.get_links(
                        "XMPP",
                        req['os'],
                        req['lc']
                    )
                    reply = self._get_msg('links', 'en')
                    reply = reply % (req['os'], req['lc'], links)

                    status = 'success'

        except (core.ConfigError, core.InternalError) as e:
            # if core failes, send the user an error message, but keep going
            self.log.error("Something went wrong internally: %s" % str(e))
            status = 'core_error'
            reply = self._get_msg('internal_error', req['lc'])

        finally:
            # keep stats
            if req:
                self.log.debug("Adding request to database... ")
                self.core.add_request_to_db()

            if reply:
                self.log.debug("Everything seems OK. Sending back the reply")
            else:
                self.log.debug("Nothing to reply!")
            return reply
