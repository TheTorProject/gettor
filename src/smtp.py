import os
import re
import sys
import email
import logging
import ConfigParser

import gettor


class SingleLevelFilter(logging.Filter):
    """
    Filter logging levels to create separated logs.

    Public methods:
        filter(record)
    """

    def __init__(self, passlevel, reject):
        """
        Initialize a new object with level to be filtered.

        If reject value is false, all but the passlevel will be
        filtered. Useful for logging in separated files.
        """

        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        """
            Do the actual filtering.
        """
        if self.reject:
            return (record.levelno != self.passlevel)
        else:
            return (record.levelno == self.passlevel)


class SMTP(object):
    """
    Class for the GetTor's SMTP service. Provides an interface to
    interact with requests received by email.
    """

    def __init__(self, config):
    	"""
        Creates new object by reading a configuration file.

        Args:

        - config (string): the path of the file that will be used as
                           configuration
        """
        logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")
        logger = logging.getLogger(__name__)

        self.delay = True
        self.logdir = 'smtp/log/'
        self.loglevel = 'DEBUG'

        # Better log format
        string_format = '[%(levelname)7s] %(asctime)s - %(message)s'
        formatter = logging.Formatter(string_format, '%Y-%m-%d %H:%M:%S')

        # Keep logs separated (and filtered)
        # all.log depends on level specified on configuration file
        all_log = logging.FileHandler(os.path.join(self.logdir, 'all.log'),
                                      mode='a+')
        all_log.setLevel(logging.getLevelName(self.loglevel))
        all_log.setFormatter(formatter)

        debug_log = logging.FileHandler(os.path.join(self.logdir, 'debug.log'),
                                        mode='a+')
        debug_log.setLevel('DEBUG')
        debug_log.addFilter(SingleLevelFilter(logging.DEBUG, False))
        debug_log.setFormatter(formatter)

        info_log = logging.FileHandler(os.path.join(self.logdir, 'info.log'),
                                       mode='a+')
        info_log.setLevel('INFO')
        info_log.addFilter(SingleLevelFilter(logging.INFO, False))
        info_log.setFormatter(formatter)

        warn_log = logging.FileHandler(os.path.join(self.logdir, 'warn.log'),
                                       mode='a+')
        warn_log.setLevel('WARNING')
        warn_log.addFilter(SingleLevelFilter(logging.WARNING, False))
        warn_log.setFormatter(formatter)

        error_log = logging.FileHandler(os.path.join(self.logdir, 'error.log'),
                                        mode='a+')
        error_log.setLevel('ERROR')
        error_log.addFilter(SingleLevelFilter(logging.ERROR, False))
        error_log.setFormatter(formatter)

        logger.addHandler(all_log)
        logger.addHandler(info_log)
        logger.addHandler(debug_log)
        logger.addHandler(warn_log)
        logger.addHandler(error_log)

        self.logger = logger
        self.logger.setLevel(logging.getLevelName(self.loglevel))
        logger.debug('Redirecting logging to %s' % self.logdir)

        # Stop logging on stdout from now on
        logger.propagate = False
        self.logger.debug("New smtp object created")

    def _log_request(self):
        """
        Logs a given request

        This should be called when something goes wrong. It saves the
        email content that triggered the malfunctioning

        Raises:

        - RuntimeError: if something goes wrong while trying to save the
                        email
        """
        self.logger.debug("Logging the mail content...")

    def _check_blacklist(self):
        """
        Check if an email is blacklisted

        It opens the corresponding blacklist file and search for the
        sender address.

        Raises:

        - BlacklistError: if the user is blacklisted.
        """
        self.logger.debug("Checking if address %s is blacklisted" %
                          self.from_addr)

    def _get_locale(self):
        """
        Get the locale from an email address

        It process the email received and look for the locale in the
        recipient address (e.g. gettor+en@torproject.org)

        If no locale found, english by default

        Returns a string containing the locale
        """
        self.logger.debug("Trying to obtain locale from recipient address")

        # If no match found, english by default
        locale = 'en'

        # Look for word+locale@something
        # Should we specify gettor and torproject?
        m = re.match('\w+\+(\w\w)@', self.to_addr)
        if m:
            self.logger.debug("Request for locale %s" % m.groups())
            locale = "%s" % m.groups()

        return locale

    def _parse_email(self):
        """
        Parses the email received

        It obtains the locale and parse the text for the rest of the info

        Returns a 4-tuple with locale, package, os and type
        """
        self.logger.debug("Parsing email")

        locale = self._get_locale()
        req_type, req_pkg, req_os = self._parse_text()

        request = {}
        request['locale'] = locale
        request['package'] = req_pkg
        request['type'] = req_type
        request['os'] = req_os

        return request

    def _parse_text(self):
        """
        Parses the text part of the email received

        It tries to figure out what the user is asking, namely, the type
        of request, the package and os required (if applies)

        Returns a 3-tuple with the type of request, package and os
        """
        self.logger.debug("Parsing email text part")

        return ('links', 'pkg', 'linux')

    def _create_email(self, msg):
        """
        Creates an email object

        This object will be used to construct the reply

        Returns the email object
        """
        self.logger.debug("Creating email object for replying")

    def _send_email(self, msg):
        """
        Send email with msg as content
        """
        self._create_email(msg)
        self.logger.debug("Email sent")

    def _send_delay(self):
        """
        Send delay message

        If delay is setted on configuration, then sends a reply to the
        user saying that the package is on the way
        """
        self.logger.debug("Sending delay message...")
        self._send_email("delay")

    def _send_links(self, links):
        """
        Send the links to the user
        """
        self.logger.debug("Sending links...")
        self._send_email(links)

    def _send_help(self):
        """
        Send help message to the user
        """
        self.logger.debug("Sending help...")
        self._send_email("help")

    def process_email(self, raw_msg):
        """
        Process the email received.

        It create an email object from the string received. The processing
        flow is as following:
            - Check for blacklisted address
            - Parse the email
            - Check the type of request
            - Send reply

        Raise:
            - ValueError if the address is blacklisted, or if the request
            asks for unsupported locales and/or operating systems, or if
            it's not possible to recognize what type of request (help, links)
            the user is asking

            - InternalError if something goes wrong while trying to obtain
            the links from the Core
        """
        self.parsed_msg = email.message_from_string(raw_msg)
        # Just for easy access
        # Normalize pending
        self.from_addr = self.parsed_msg['From']
        self.to_addr = self.parsed_msg['To']

        # We have the info we need on self.parsed_msg
        try:
            self._check_blacklist()
        except ValueError as e:
            raise ValueError("The address %s is blacklisted!" %
                             self.from_addr)

        # Try to figure out what the user is asking
        request = self._parse_email()

        # Two possible options: asking for help or for the links
        # If not, it means malformed message, and no default values
        self.logger.info("New request for %s" % request['type'])
        if request['type'] == 'help':
            self._send_help(request['locale'])
        elif request['type'] == 'links':
            if self.delay:
                self._send_delay()

            try:
                self.logger.info("Asking Core for links in %s for %s" %
                                 (request['locale'], request['os']))
                # links = self.core.get_links(request['os'], request['locale'])
                links = "dummy links"
                self._send_links(links)
            except ValueError as e:
                raise ValueError(str(e))
            except RuntimeError as e:
                raise RuntimeError(str(e))
        else:
            raise ValueError("Malformed message. No default values either")
