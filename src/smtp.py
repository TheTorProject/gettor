import os
import re
import sys
import time
import email
import gettext
import hashlib
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

    def __init__(self, config_file):
    	"""
        Create new object by reading a configuration file.

        Args:

        - config (string): the path of the file that will be used as
                           configuration
        """
        logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")
        logger = logging.getLogger(__name__)
        config = ConfigParser.ConfigParser()

        if os.path.isfile(config_file):
            logger.info("Reading configuration from %s" % config_file)
            config.read(config_file)
        else:
            logger.error("Error while trying to read %s" % config_file)
            raise RuntimeError("Couldn't read the configuration file %s"
                               % config_file)

        # Handle the gets internally to catch proper exceptions
        try:
            self.basedir = self._get_config_option('general',
                                                   'basedir', config)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.delay = self._get_config_option('general',
                                                 'delay', config)
            # There has to be a better way for this...
            if self.delay == 'False':
                self.delay = False

        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.our_addr = self._get_config_option('general',
                                                    'our_addr', config)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.logdir = self._get_config_option('log',
                                                  'dir', config)
            self.logdir = os.path.join(self.basedir, self.logdir)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.logdir_emails = self._get_config_option('log',
                                                         'emails_dir',
                                                         config)
            self.logdir_emails = os.path.join(self.logdir, self.logdir_emails)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.loglevel = self._get_config_option('log',
                                                    'level', config)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        self.core = gettor.Core('gettor.cfg')

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

    def _get_sha1(self, string):
        """
        Get the sha1 of a string

        Used whenever we want to do things with addresses (log, blacklist, etc)

        Returns a string
        """
        return str(hashlib.sha1(string).hexdigest())

    def _log_request(self, addr, content):
        """
        Log a given request

        This should be called when something goes wrong. It saves the
        email content that triggered the malfunctioning

        Raises:

        - RuntimeError: if something goes wrong while trying to save the
                        email
        """
        # We don't store the original address, but rather its sha1 digest
        # in order to know when some specific addresses are doing weird
        # requests
        log_addr = self._get_sha1(addr)
        filename = str(time.time()) + '.log'
        path = self.logdir_emails + filename
        abs_path = os.path.abspath(path)

        log_file = open(abs_path, 'w+')
        log_file.write(content)
        log_file.close()

        self.logger.debug("Logging request from %s in %s"
                          % (log_addr, abs_path))

    def _check_blacklist(self, addr):
        """
        Check if an email is blacklisted

        It opens the corresponding blacklist file and search for the
        sender address.

        Raises:

        - BlacklistError: if the user is blacklisted.
        """
        anon_addr = self._get_sha1(addr)
        self.logger.debug("Checking if address %s is blacklisted" %
                          anon_addr)

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

        # Look for gettor+locale@torproject.org
        m = re.match('gettor\+(\w\w)@torproject\.org', self.to_addr)
        if m:
            self.logger.debug("Request for locale %s" % m.groups())
            locale = "%s" % m.groups()

        return locale

    def _get_normalized_address(self, addr):
        """
        Get normalized address

        It looks for anything inside the last '<' and '>'. Code taken
        from the old GetTor (utils.py)

        On success, returns the normalized address
        On failure, returns ValueError
        """
        if '<' in addr:
            idx = addr.rindex('<')
            addr = addr[idx:]
            m = re.search(r'<([^>]*)>', addr)
            if m is None:
                raise ValueError("Couldn't extract normalized address from %s"
                                 % addr)
            addr = m.group(1)
        return addr

    def _parse_email(self):
        """
        Parse the email received

        It obtains the locale and parse the text for the rest of the info

        Returns a 3-tuple with locale, os and type
        """
        self.logger.debug("Parsing email")

        locale = self._get_locale()
        request = self._parse_text()
        request['locale'] = locale

        return request

    def _parse_text(self):
        """
        Parse the text part of the email received

        It tries to figure out what the user is asking, namely, the type
        of request, the package and os required (if applies)

        Returns a tuple with the type of request and os (None if request
        is for help)
        """
        self.logger.debug("Parsing email text part")

        # By default we asume the request is asking for links
        request = {}
        request['type'] = 'links'
        request['os'] = None

        # The core knows what OS are supported
        supported_os = self.core.get_supported_os()

        lines = self.raw_msg.split('\n')
        found_os = False
        for line in lines:
            # Check for help request
            if re.match('.*help.*', line, re.IGNORECASE):
                request['type'] = 'help'
                break
            # Check for os
            for supported in supported_os:
                p = '.*' + supported + '.*'
                if re.match(p, line, re.IGNORECASE):
                    request['os'] = supported
                    found_os = True
            if found_os:
                break

            if request['type'] == 'links' and not request['os']:
                # Windows by default?
                request['os'] = 'windows'

        return request

    def _create_email(self, from_addr, to_addr, subject, msg):
        """
        Create an email object

        This object will be used to construct the reply. Comment lines
        331-334, 339, and uncomment lines 336, 337, 340 to test it
        without having an SMTP server

        Returns the email object
        """
        self.logger.debug("Creating email object for replying")
        # email_obj = MIMEtext(msg)
        # email_obj['Subject'] = subject
        # email_obj['From'] = from_addr
        # email_obj['To'] = to_addr

        reply = "From: " + from_addr + ", To: " + to_addr
        reply = reply + ", Subject: " + subject + "\n\n" + msg

        # return email_obj
        return reply

    def _send_email(self, from_addr, to_addr, subject, msg):
        """
        Send an email

        It takes a from and to addresses, a subject and the content, creates
        an email and send it. Comment lines 350-352 and uncomment line 353
        to test it without having an SMTP server
        """
        email_obj = self._create_email(from_addr, to_addr, subject, msg)
        # s = smtplib.SMTP("localhost")
        # s.sendmail(from_addr, to_addr, msg.as_string())
        # s.quit()
        print email_obj
        self.logger.debug("Email sent")

    def _send_delay(self, locale, from_addr, to_addr):
        """
        Send delay message

        If delay is setted on configuration, then sends a reply to the
        user saying that the package is on the way
        """
        self.logger.debug("Delay is setted. Sending a delay message.")

        # Obtain the content in the proper language and send it
        t = gettext.translation(locale, './i18n', languages=[locale])
        _ = t.ugettext

        delay_msg = _('delay_msg')
        delay_subject = _('delay_subject')
        self._send_email(from_addr, to_addr, delay_subject, delay_msg)

    def _send_links(self, links, locale, from_addr, to_addr):
        """
        Send the links to the user

        It gets the message in the proper language (according to the
        locale), replace variables in that message and call to send the
        email
        """
        self.logger.debug("Request for links in %s" % locale)

        # Obtain the content in the proper language and send it
        t = gettext.translation(locale, './i18n', languages=[locale])
        _ = t.ugettext

        links_msg = _('links_msg')
        links_subject = _('links_subject')
        links_msg = links_msg % ('linux', locale, links, links)
        self._send_email(from_addr, to_addr, links_subject, links_msg)

    def _send_help(self, locale, from_addr, to_addr):
        """
        Send help message to the user

        It gets the message in the proper language (according to the
        locale), replace variables in that message (if any) and call to send
        the email
        """
        self.logger.debug("Request for help in %s" % locale)

        # Obtain the content in the proper language and send it
        t = gettext.translation(locale, './i18n', languages=[locale])
        _ = t.ugettext

        help_msg = _('help_msg')
        help_subject = _('help_subject')
        self._send_email(from_addr, to_addr, help_subject, help_msg)

    def process_email(self, raw_msg):
        """
        Process the email received.

        It creates an email object from the string received. The processing
        flow is as following:
            - Check for blacklisted address
            - Parse the email
            - Check the type of request
            - Send reply

        Raises:
            - ValueError if the address is blacklisted, or if the request
            asks for unsupported locales and/or operating systems, or if
            it's not possible to recognize what type of request (help, links)
            the user is asking

            - InternalError if something goes wrong while trying to obtain
            the links from the Core
        """
        self.raw_msg = raw_msg
        self.parsed_msg = email.message_from_string(raw_msg)
        # Just for easy access
        self.from_addr = self.parsed_msg['From']
        self.norm_from_addr = self._get_normalized_address(self.from_addr)
        self.to_addr = self.parsed_msg['To']

        # We have the info we need on self.parsed_msg
        try:
            self._check_blacklist(self._get_sha1(self.from_addr))
        except ValueError as e:
            raise ValueError("The address %s is blacklisted!" %
                             self._get_sha1(self.from_addr))

        # Try to figure out what the user is asking
        request = self._parse_email()

        # Two possible options: asking for help or for the links
        # If not, it means malformed message, and no default values
        self.logger.info("New request for %s" % request['type'])
        if request['type'] == 'help':
            self._send_help(request['locale'], self.our_addr,
                            self.norm_from_addr)
        elif request['type'] == 'links':
            if self.delay:
                self._send_delay(request['locale'], self.our_addr,
                                 self.norm_from_addr)

            try:
                self.logger.info("Asking Core for links in %s for %s" %
                                 (request['locale'], request['os']))

                links = self.core.get_links('SMTP', request['os'],
                                            request['locale'])

                self._send_links(links, request['locale'], self.our_addr,
                                 self.norm_from_addr)
            except ValueError as e:
                raise ValueError(str(e))
            except RuntimeError as e:
                raise RuntimeError(str(e))
        else:
            raise ValueError("Malformed message. No default values either")

    def _get_config_option(self, section, option, config):
        """
            Private method to get configuration options.

            It tries to obtain a value from a section in config using
            ConfigParser. It catches possible exceptions and raises
            RuntimeError if something goes wrong.

            Arguments:
                config: ConfigParser object
                section: section inside config
                option: option inside section

            Returns the value of the option inside the section in the
            config object.
        """

        try:
            value = config.get(section, option)
            return value
        # This exceptions should appear when messing with the configuration
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError,
                ConfigParser.InterpolationError,
                ConfigParser.MissingSectionHeaderError,
                ConfigParser.ParsingError) as e:
            raise RuntimeError("%s" % str(e))
        # No other errors should occurr, unless something's terribly wrong
        except ConfigParser.Error as e:
            raise RuntimeError("Unexpected error: %s" % str(e))
