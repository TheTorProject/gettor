# -*- coding: utf-8 -*-
#
# This file is part of GetTor.
#
# :authors: Israel Leiva <ilv@torproject.org>
#           Based on BridgeDB Twitter distributor (PoC) by wfn
#           - https://github.com/wfn/twidibot
#
# :copyright:   (c) 2008-2015, The Tor Project, Inc.
#               (c) 2015, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

import os
import re
import tweepy
import logging
import gettext
import ConfigParser

import core
import utils
import blacklist

"""Twitter channel for distributing links to download Tor Browser."""


class ConfigError(Exception):
    pass


class InternalError(Exception):
    pass


class GetTorStreamListener(tweepy.StreamListener):
    """ Basic listener for Twitter's streaming API."""
    def __init__(self, bot):
        self.bot = bot
        super(GetTorStreamListener, self).__init__(self.bot.api)

    def on_direct_message(self, status):
        """ Right now we only care about direct messages. """
        if status.direct_message['sender']['id_str'] != self.bot.bot_info.id_str:
            self.bot.parse_request(status.direct_message)


class TwitterBot(object):
    """ Receive and reply requests via Twitter. """
    def __init__(self, cfg=None):
        """ Create new object by reading a configuration file.

        :param: cfg (string) the path of the configuration file.
        """

        default_cfg = 'twitter.cfg'
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = default_cfg

        try:
            with open(cfg) as f:
                config.readfp(f)
        except IOError:
            raise ConfigError("File %s not found!" % cfg)

        try:
            self.api_key = config.get('access_config', 'api_key')
            self.api_secret = config.get('access_config', 'api_secret')
            self.access_token = config.get('access_config', 'access_token')
            self.token_secret = config.get('access_config', 'token_secret')

            self.mirrors = config.get('general', 'mirrors')
            self.i18ndir = config.get('i18n', 'dir')

            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'twitter.log')
            loglevel = config.get('log', 'level')

            blacklist_cfg = config.get('blacklist', 'cfg')
            self.bl = blacklist.Blacklist(blacklist_cfg)
            self.bl_max_request = config.get('blacklist', 'max_requests')
            self.bl_max_request = int(self.bl_max_request)
            self.bl_wait_time = config.get('blacklist', 'wait_time')
            self.bl_wait_time = int(self.bl_wait_time)

            core_cfg = config.get('general', 'core_cfg')
            self.core = core.Core(core_cfg)

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

        log.info('Redirecting Twitter logging to %s' % logfile)
        logfileh = logging.FileHandler(logfile, mode='a+')
        logfileh.setFormatter(formatter)
        logfileh.setLevel(logging.getLevelName(loglevel))
        log.addHandler(logfileh)

        self.log = log

    def _is_blacklisted(self, username):
        """Check if a user is blacklisted.

        :param: addr (string) the hashed username.

        :return: true is the username is blacklisted, false otherwise.

        """
        hashed_username = utils.get_sha256(username)

        try:
            self.bl.is_blacklisted(
                hashed_username,
                'Twitter',
                self.bl_max_request,
                self.bl_wait_time
            )
            return False
        except blacklist.BlacklistError as e:
            return True

    def _get_msg(self, msgid, lc):
        """Get message identified by msgid in a specific locale.

        Params: msgid: the identifier of a string.
                lc: the locale.

        Return: a string containing the given message.

        """
        try:
            t = gettext.translation(lc, self.i18ndir, languages=[lc])
            _ = t.ugettext

            msgstr = _(msgid)
            return msgstr
        except IOError as e:
            raise ConfigError("%s" % str(e))

    def parse_text(self, msg):
        """ Parse the text part of a message.

        Split the message in words and look for patterns for locale,
        operating system and mirrors requests.

        :param: msg (string) the message received.

        :return: request (list) 3-tuple with locale, os and type of request.
        """

        # core knows what OS are supported
        supported_os = self.core.get_supported_os()
        supported_lc = self.core.get_supported_lc()

        # default values
        req = {}
        req['lc'] = 'en'
        req['os'] = None
        req['type'] = 'help'

        found_lc = False
        found_os = False
        found_mirrors = False

        # analyze every word
        words = re.split('\s+', msg.strip())
        for word in words:
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

    def parse_request(self, dm):
        """ Process the request received.

        Check if the user is not blacklisted and then check the body of
        the message to find out what is asking.

        :param: dm (status.direct_message) the direct message object received
                via Twitter API.

        """

        sender_id = dm['sender']['id_str']
        msg = dm['text'].strip().lower()
        bogus_request = False
        request = None
        status = ''

        try:
            if self._is_blacklisted(str(sender_id)):
                self.log.info('blacklist; none; none')
                bogus_request = True

            if not bogus_request:
                self.log.debug("Request seems legit, let's parse it")
                # let's try to guess what the user is asking
                request = self.parse_text(str(msg))

                # possible options: links, mirrors, help
                if request['type'] == 'links':
                    self.log.info('links; %s; %s' % (req['os'], req['lc']))
                    links = self.core.get_links(
                        'Twitter',
                        request['os'],
                        request['lc']
                    )

                    reply = self._get_msg('links', 'en')
                    reply = reply % (request['os'], request['lc'], links)

                elif request['type'] == 'mirrors':
                    self.log.info('mirrors; none; %s' % req['lc'])
                    reply = self._get_msg('mirrors', 'en')
                    try:
                        with open(self.mirrors, "r") as list_mirrors:
                            mirrors = list_mirrors.read()
                        reply = reply % mirrors

                    except IOError as e:
                        reply = self._get_msg('mirrors_unavailable', 'en')

                else:
                    self.log.info('help; none; %s' % req['lc'])
                    reply = self._get_msg('help', 'en')

                self.api.send_direct_message(
                    user_id=sender_id,
                    text=reply
                )

        except (core.ConfigError, core.InternalError) as e:
            # if core failes, send the user an error message, but keep going
            self.log.error("Something went wrong internally: %s" % str(e))
            reply = self._get_msg('internal_error', 'en')

    def start(self):
        """ Start the bot for handling requests.

        Start a new Twitter bot.
        """
        self.auth = tweepy.OAuthHandler(
            self.api_key,
            self.api_secret
        )

        self.auth.set_access_token(
            self.access_token,
            self.token_secret
        )

        self.api = tweepy.API(self.auth)
        self.bot_info = self.api.me()

        stream = tweepy.Stream(
            auth=self.api.auth,
            listener=GetTorStreamListener(self)
        )

        stream.userstream()
