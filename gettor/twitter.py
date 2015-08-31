# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: Israel Leiva <ilv@riseup.net>
#           Based on BridgeDB Twitter distributor (PoC) by wfn
#           - https://github.com/wfn/twidibot
#
# :copyright:   (c) 2008-2015, The Tor Project, Inc.
#               (c) 2015, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

import sys
import json
import time
import signal
import tweepy
import gettext

from tweepy.models import Status

import core
import utils
import blacklist

"""Twitter module for processing requests. Forked from BridgeDB Twitter
distributor by wfn (https://github.com/wfn/twidibot)"""


class ConfigError(Exception):
    pass


class InternalError(Exception):
    pass


class TwitterBotStreamListener(tweepy.StreamListener):
    """Listener for twitter's Streaming API."""

    def __init__(self, bot, api=None):
        self.bot = bot
        self.processing_data = False

        super(TwitterBotStreamListener, self).__init__(api)

    def on_data(self, raw_data):
        """Called when raw data is received from connection.

        This is where all the data comes first. Normally we could use 
        (inherit) the on_data() in tweepy.StreamListener, but it unnecessarily
        and naively reports unknown event types as errors (to simple log); 
        also, we might want to tweak it further later on.

        But for now, this is basically taken from tweepy's on_data().

        Return False to stop stream and close connection.

        """

        self.processing_data = True

        data = json.loads(raw_data)

        if 'in_reply_to_status_id' in data:
            status = Status.parse(self.api, data)
            if self.on_status(status) is False:
                return False
        elif 'delete' in data:
            delete = data['delete']['status']
            if self.on_delete(delete['id'], delete['user_id']) is False:
                return False
        elif 'event' in data:
            status = Status.parse(self.api, data)
            if self.on_event(status) is False:
                return False
        elif 'direct_message' in data:
            status = Status.parse(self.api, data)
            if self.on_direct_message(status) is False:
                return False
        elif 'limit' in data:
            if self.on_limit(data['limit']['track']) is False:
                return False
        elif 'disconnect' in data:
            if self.on_disconnect(data['disconnect']) is False:
                return False
        else:
            # we really are ok to receive unknown stream/event types.
            # log to debug?
            log.debug('TwitterBotStreamListener::on_data(): got event/stream'
                    ' data of unknown type. Raw data follows:\n%s', data)

        self.processing_data = False

    def on_status(self, status):
        """Called when a new status arrives"""

        #log.debug('Got status: %s', status)
        return

    def on_event(self, status):
        """Called when a new event arrives"""

        #log.debug('Got event: %s', status)

        # XXX make sure tweepy's given 'status.event' unicode string can
        # always be safely converted to ascii
        
        # now it seems one can reply to dm without following the account
        # if str(status.event) == 'follow':  
        #    self.bot.handleFollowEvent(status)

        return

    def on_direct_message(self, status):
        """Called when a new direct message arrives or is sent from us

        TODO: make a pull request for tweepy or something, because they 
        say it's only when a direct message is *received* (implying, 'by us')

        """

        # doing twitter user comparisons using id_str makes sense here - it's
        # safe and id_str's are guaranteed to be unique (re: latter, just like
        # id's.) maybe consider deciding how comparisons should be made for sure,
        # and then extend tweepy.models.User to include __eq__?
        if status.direct_message['sender']['id_str'] != self.bot.bot_info.id_str:
            self.bot.handleDirectMessage(status)
        else:
            # log.debug('Caught a direct message sent *from* us')
            pass

        return

    def on_connect(self):
        """Called once connected to streaming server.

        This will be invoked once a successful response
        is received from the server. Allows the listener
        to perform some work prior to entering the read loop.

        """
        pass

    def on_exception(self, exception):
        """Called when an unhandled exception occurs."""
        return

    def on_delete(self, status_id, user_id):
        """Called when a delete notice arrives for a status"""
        return

    def on_limit(self, track):
        """Called when a limitation notice arrvies"""
        return

    def on_error(self, status_code):
        """Called when a non-200 status code is returned"""
        return False

    def on_timeout(self):
        """Called when stream connection times out"""
        return

    def on_disconnect(self, notice):
        """Called when twitter sends a disconnect notice

        Disconnect codes are listed here:
        https://dev.twitter.com/docs/streaming-apis/messages
            #Disconnect_messages_disconnect

        """
        return
    

class TwitterBot(object):
    """Main interface between the stateful listener and Twitter APIs."""

    # TODO: think about secure ways of storing twitter access config.
    # For one, app itself should ideally not be able to have write access
    # to it. For another, ideally it would request details from some other
    # component, authenticate, and not be able to re-authenticate to twitter
    
    """
    default_access_config = {
        'api_key': config.API_KEY,
        'api_secret': config.API_SECRET,
        'access_token': config.ACCESS_TOKEN,
        'token_secret': config.TOKEN_SECRET
    }"""

    def __init__(self, **kw):
        """Constructor that accepts custom access config as named arguments

        Easy to test things from interactive shell this way.
        Probably won't be needed in production code.

        """

        """
        self.access_config = dict()
        for key, default in self.default_access_config.iteritems():
            self.access_config[key] = kw.get(key, default)
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

            self.async_streaming = config.get('api', 'async_streaming')
            self.char_limit = config.get('api', 'char_limit')

            self.mirrors = config.get('general', 'mirrors')
            self.max_words = config.get('general', 'max_words')
            self.i18ndir = config.get('i18n', 'dir')

            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'twitter.log')
            loglevel = config.get('log', 'level')

            blacklist_cfg = config.get('blacklist', 'cfg')
            self.bl = blacklist.Blacklist(blacklist_cfg)
            self.bl_max_req = config.get('blacklist', 'max_requests')
            self.bl_max_req = int(self.bl_max_req)
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

        log.info('Redirecting SMTP logging to %s' % logfile)
        logfileh = logging.FileHandler(logfile, mode='a+')
        logfileh.setFormatter(formatter)
        logfileh.setLevel(logging.getLevelName(loglevel))
        log.addHandler(logfileh)

        # stop logging on stdout from now on
        log.propagate = False
        self.log = log

        self.setSignalHandlers()
        self.msg = Messages()


    def _is_blacklisted(self, account):
        """Check if a user is blacklisted.

        :param: addr (string) the hashed address of the user.

        :return: true is the address is blacklisted, false otherwise.

        """
        anon_acc = utils.get_sha256(account)

        try:
            self.bl.is_blacklisted(
                anon_acc, 'Twitter', self.bl_max_req, self.bl_wait_time
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
        self.log.debug("Getting message '%s' for locale %s" % (msgid, lc))
        try:
            t = gettext.translation(lc, self.i18ndir, languages=[lc])
            _ = t.ugettext

            msgstr = _(msgid)
            return msgstr
        except IOError as e:
            raise ConfigError("%s" % str(e))
    
    
    def _parse_request(self, message):
        """ """
        self.log.debug("Parsing text.")
        
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
        for word in message.split(' '):
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


    def setSignalHandlers(self):
        """Set up relevant SIG* handlers for the bot.

        Note: if we want to handle some specific signal and not exit after
        catching it, we may need to store the original CPython handler
        (signified by signal.SIG_DFL), and restore it after handling the
        signal in question. For now, we'll only care about signals after
        which the program does exit.

        """

        # for now, we'll only handle SIGTERM. it might make sense to handle
        # SIGINT as well, though.

        signal.signal(signal.SIGTERM, self.handleSIGTERM)
        self.log.debug("SIGTERM handler is set.")

    def handleSIGTERM(self, sig_number, stack_frame):
        """Callback function called upon SIGTERM"""

        self.log.info("TwitterBot::handleSIGTERM(): caught SIGTERM signal.")

        self.log.info("Stopping bot listener.")
        self.listener.running = False
        while self.listener.processing_data:
            self.log.info(
                "Waiting for TwitterBotStreamListener to finish processing"
                " a data request/package"
            )
            time.sleep(0.5)

        self.log.info("Closing down storage controller.")
        self.storage_controller.closeAll()

        self.log.info("Exiting program.")
        sys.exit(0)

    def authenticate(self, auth=None):
        """Authenticate to Twitter API, get API handle, and remember it."""

        if auth:
            self.auth = auth
        else:
            self.auth = tweepy.OAuthHandler(
                self.api_key,
                self.api_secret
            )

            self.auth.set_access_token(
                self.access_token,
                self.token_secret
            )

        try:
            self.api = tweepy.API(self.auth)
        except Exception as e:
            self.log.fatal('Exception while authenticating to Twitter and '
                           'getting API handle: %s', e)
            self.api = None
        finally:
            # del self.auth # ideally we'd be able to delete this, but 
            # presently - no; anything?
            pass

        if self.api:
            self.log.info('Authenticated and got the RESTful API handle')
            self.bot_info = self.api.me()
            #api.update_status('hello world!')

    def subscribeToStreams(self):
        """Subscribe to relevant streams in the Streaming API."""

        self.listener = TwitterBotStreamListener(
            bot=self,
            api=self.api
        )

        self.stream = tweepy.Stream(self.auth, self.listener)

        # user stream gives us direct messages and follow events
        self.stream.userstream(async=self.async_streaming)
        # stream.filter may be useful, but we don't need it for now

        # the following will not be executed if we're not going async -
        # userstream() blocks, its event handler loop takes over:
        self.log.info('Subscribed to relevant streams via Streaming API')

    def handleFollowEvent(self, event):
        """
        user_id = event.source['id']  # 'id' is unique big int

        if user_id != self.bot_info.id:
            user = self.api.get_user(id=user_id)
            user.follow()

        if config.RESPOND_AFTER_FOLLOW:
            # the following line *blocks* the thread that we care about.
            # we should not do this, ever. as long as we're just testing
            # with a few cat accounts, it's ok.
            
            # TODO: use sched.scheduler, or threading.Timer (or sth)
            time.sleep(config.WAIT_TIME_AFTER_FOLLOW) 

        # for now, english by default
        self.sendMessage(
            user_id,
            get_msg('welcome', 'en')
        )
        """
        # it seems that we don't need to be followed to send dm
        pass


    def handleDirectMessage(self, status):
        """ Handle direct messages received (i.e. parse request). """
        sender_id = status.direct_message['sender_id']
        message = status.direct_message['text'].strip().lower()

        self.log.debug("Parsing request")

        try:
            if self._is_blacklisted(str(sender_id)):
                self.log.info("Request from blacklisted account!")
                status = 'blacklisted'
                bogus_request = True

            # first let's find out how many words are in the message
            # request shouldn't be longer than 3 words, but just in case
            words = message.split(' ')
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
                        "Twitter",
                        req['os'],
                        req['lc']
                    )
                    reply = self._get_msg('links', 'en')
                    reply = reply % (req['os'], req['lc'], links)
                    self.sendMessage(sender_id, reply)

                    status = 'success'
            
            # send whatever the reply is
            self.sendMessage(sender_id, reply)

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

    def sendMessage(self, target_id, message):
        # this is quick and ugly. primary splits (if needed) at newlines.
        """
        try:
            cur_message = ''
            for line in message.split('\n'):
                if len(cur_message + ('\n' if cur_message else '') + line)\
                    > config.CHARACTER_LIMIT:
                    self._split_in_chunks_and_send(target_id, cur_message)
                    cur_message = ''
                else:
                    cur_message += ('\n' if cur_message else '') + line
            if cur_message:
                self._split_in_chunks_and_send(target_id, cur_message)
        except Exception as e:
            # again, scrubbing 'target_id' should be an option, etc.
            log.warning('Failed to send a direct message to %s. Exception:\n%s',
                        str(target_id), e)
            return False
        return True
        """
        # with new twitter limit of direct messages, we can send messages
        # without any trouble
        self.api.send_direct_message(
            user_id=target_id,
            text=message
        )

    """
    def _split_in_chunks_and_send(self, target_id, message):
        # assume any decent humane splitting has been done beforehand.
        # we have to do with what we have here.
        # exception handling at higher call stack.

        while message:
            self.api.send_direct_message(user_id=target_id,
                text=message[:config.CHARACTER_LIMIT])
            message = message[config.CHARACTER_LIMIT:]
    """

    """
    def followAllFollowers(self):
        # Start following everyone who is following us.

        for follower in tweepy.Cursor(self.api.followers).items():
            follower.follow()
    """

    """
    def unfollowAllFollowers(self):
        # Unfollow everyone who is following us.

        for follower in tweepy.Cursor(self.api.followers).items():
            follower.unfollow()
    """
