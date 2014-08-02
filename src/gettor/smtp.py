# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser Bundle distribution system.
#


import os
import re
import sys
import time
import email
import gettext
import hashlib
import logging
import ConfigParser

import utils
import core

"""SMTP module for processing email requests."""


class ConfigurationError(Exception):
    pass


class BlacklistError(Exception):
    pass


class AddressError(Exception):
    pass


class SendEmailError(Exception):
    pass


class InternalError(Exception):
    pass


class SMTP(object):
    """Receive and reply requests by email.

    Public methods:

        process_email(): Process the email received.

    Exceptions:

        ConfigurationError: Bad configuration.
        BlacklistError: Address of the sender is blacklisted.
        AddressError: Address of the sender malformed.
        SendEmailError: SMTP server not responding.
        InternalError: Something went wrong internally.

    """

    def __init__(self, cfg=None):
    	"""Create new object by reading a configuration file.

        Params: cfg - path of the configuration file.

        """
        # Define a set of default values
        DEFAULT_CONFIG_FILE = 'smtp.cfg'

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
            self.basedir = config.get('general', 'basedir')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'basedir' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.delay = config.get('general', 'delay')
            # There has to be a better way for doing this...
            if self.delay == 'False':
                self.delay = False

        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'delay' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.our_addr = config.get('general', 'our_addr')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'our_addr' from 'general' (%s)" %
                           cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.logdir = config.get('log', 'dir')
            self.logdir = os.path.join(self.basedir, self.logdir)
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'dir' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.logdir_emails = config.get('log', 'emails_dir')
            self.logdir_emails = os.path.join(self.logdir, self.logdir_emails)
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'emails_dir' from 'log' (%s)" % cfg)
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
        self.logger.debug("New smtp object created")

    def _get_sha1(self, string):
        """Get sha1 of a string.

        Used whenever we want to do things with addresses (log, blacklist,
        etc.)

        Params: The string to be sha1'ed.

        Returns: sha1 of string.

        """
        return str(hashlib.sha1(string).hexdigest())

    def _log_request(self, addr, raw_msg):
        """Log a request.

        This should be called when something goes wrong. It saves the
        email content that triggered the malfunctioning.

        Raises: InternalError: if something goes wrong while trying to
                save the email.

        Params: addr - The address of the sender.
                content - The content of the email received.

        """

        # to do: obtain content of msg, not the entire email
        content = raw_msg

        # We store the sha1 of the original address in order to know when
        # specific addresses are doing weird requests
        log_addr = self._get_sha1(addr)
        filename = str(time.time()) + '.log'
        path = self.logdir_emails + filename
        abs_path = os.path.abspath(path)

        if os.path.isfile(abs_path):
            log_file = open(abs_path, 'w+')
            log_file.write(content)
            log_file.close()
            self.logger.debug("Logging request from %s in %s" %
                              (log_addr, abs_path))
        else:
            self.logger.warning("Couldn't open emails' log file (%s)" %
                                abs_path)
            raise InternalError("Error while saving the email content.")

    def _check_blacklist(self, addr):
        """Check if an email address is blacklisted.

        Look for the address in the file of blacklisted addresses.

        Raises: BlacklistError if the user is blacklisted.

        Params: addr - the address we want to check.

        """
        anon_addr = self._get_sha1(addr)
        self.logger.debug("Checking if address %s is blacklisted" %
                          anon_addr)

        # if blacklisted:
        #    raise BlacklistError("Address %s is blacklisted!" % anon_addr)

    def _get_locale(self, addr):
        """Get the locale from an email address.

        Process the email received and look for the locale in the recipient
        address (e.g. gettor+en@torproject.org). If no locale found, english
        by default.

        Params: The email address we want to get the locale.

        Returns: String containing the locale.

        """
        self.logger.debug("Trying to obtain locale from recipient address")

        # If no match found, english by default
        locale = 'en'

        # Look for gettor+locale@torproject.org
        m = re.match('gettor\+(\w\w)@torproject\.org', addr)
        if m:
            self.logger.debug("Request for locale %s" % m.groups())
            locale = "%s" % m.groups()

        return locale.lower()

    def _get_normalized_address(self, addr):
        """Get normalized address.

        We look for anything inside the last '<' and '>'. Code taken from
        the old GetTor (utils.py).

        Raises: AddressError: if address can't be normalized.

        Params: addr - the address we want to normalize.

        Returns: String with the normalized address on success.

        """
        if '<' in addr:
            idx = addr.rindex('<')
            addr = addr[idx:]
            m = re.search(r'<([^>]*)>', addr)
            if m is None:
                raise AddressError("Couldn't extract normalized address "
                                   "from %s" % self_get_sha1(addr))
            addr = m.group(1)
        return addr

    def _parse_email(self, raw_msg, addr):
        """Parse the email received.

        Get the locale and parse the text for the rest of the info.

        Params: raw_msg - content of the email to be parsed.
                addr - address of the recipient (i.e. us).

        Returns: a 3-tuple with locale, os and type.

        """
        self.logger.debug("Parsing email")

        request = self._parse_text(raw_msg)
        locale = self._get_locale(addr)
        request['locale'] = locale

        return request

    def _parse_text(self, raw_msg):
        """Parse the text part of the email received.

        Try to figure out what the user is asking, namely, the type
        of request, the package and os required (if applies).

        Params: raw_msg - content of the email to be parsed.

        Returns: Tuple with the type of request and os
                 (None if request is for help).
        """
        self.logger.debug("Parsing email text part")

        # By default we asume the request is asking for help
        request = {}
        request['type'] = 'help'
        request['os'] = None

        # core knows what OS are supported
        supported_os = self.core.get_supported_os()

        lines = raw_msg.split('\n')
        found_os = False
        for line in lines:
            # Check for help request
            if re.match('.*help.*', line, re.IGNORECASE):
                self.logger.info("Request for help found")
                request['type'] = 'help'
                break
            # Check for os
            if not found_os:
                for supported in supported_os:
                    p = '.*' + supported + '.*'
                    if re.match(p, line, re.IGNORECASE):
                        request['os'] = supported
                        request['type'] = 'links'
                        self.logger.debug("Request for links found")
                        found_os = True
                        break
            # Check if the user is asking for terms related to pt
            if re.match("[obfs|plugabble transport|pt]", line, re.IGNORECASE):
                self.logger.info("Request for PT found")
                request['pt'] = True

        return request

    def _create_email(self, from_addr, to_addr, subject, msg):
        """Create an email object.

        This object will be used to construct the reply.

        Params: from_addr - address of the sender.
                to_addr - address of the recipient.
                subject - subject of the email.
                msg - content of the email.

        Returns: The email object.

        """
        self.logger.debug("Creating email object for replying")
        # try:
        #   email_obj = MIMEtext(msg)
        #   email_obj['Subject'] = subject
        #   email_obj['From'] = from_addr
        #   email_obj['To'] = to_addr

        reply = "From: " + from_addr + ", To: " + to_addr
        reply = reply + ", Subject: " + subject + "\n\n" + msg

        # return email_obj
        return reply

    def _send_email(self, from_addr, to_addr, subject, msg):
        """Send an email.

        Take a 'from' and 'to' addresses, a subject and the content, creates
        the email and send it.

        Params: from_addr - address of the sender.
                to_addr - address of the recipient.
                subject - subject of the email.
                msg - content of the email.

        """
        email_obj = self._create_email(from_addr, to_addr, subject, msg)
        # try:
        #   s = smtplib.SMTP("localhost")
        #   s.sendmail(from_addr, to_addr, msg.as_string())
        #   s.quit()
        # except SMTPException as e:
        #   self.logger.error("Couldn't send the email: %s" % str(e))
        #   raise SendEmailError("Error with SMTP: %s" % str(e))
        print email_obj
        self.logger.debug("Email sent")

    def _send_delay(self, locale, from_addr, to_addr):
        """Send delay message.

        If the config says so, send a delay message.

        Params: locale - two-character string describing a locale.
                from_addr - address of the sender.
                to_addr - address of the recipient.

        """
        self.logger.debug("Delay is ON. Sending a delay message.")

        # Obtain the content in the proper language and send it
        t = gettext.translation(locale, './i18n', languages=[locale])
        _ = t.ugettext

        delay_subject = _('delay_subject')
        delay_msg = _('delay_msg')

        try:
            self._send_email(from_addr, to_addr, delay_subject, delay_msg)
        except SendEmailError as e:
            self.logger.warning("Couldn't send delay message")
            raise InternalError("Error while sending delay message")

    def _send_links(self, links, locale, operating_system, from_addr, to_addr,
                    pt):
        """Send links to the user.

        Get the message in the proper language (according to the locale),
        replace variables and send the email.

        Params: links - links to be sent.
                locale - two-character string describing a locale.
                from_addr - address of the sender.
                to_addr - address of the recipient.
                pt - True/False if the user did a PT request.

        """
        self.logger.debug("Request for links in %s" % locale)

        # Obtain the content in the proper language and send it
        t = gettext.translation(locale, './i18n', languages=[locale])
        _ = t.ugettext

        links_subject = _('links_subject')
        links_msg = _('links_msg')
        links_msg = links_msg % (operating_system, locale, links, links)
        
        # Don't forget to check if user did a PT request
        if pt:
            # If so, we get the links message + info about PT included.
            links_subject = _('links_pt_subject')
            links_msg = _('links_pt_msg')
            links_msg = links_msg % (operating_system, locale, links, links)

        try:
            self._send_email(from_addr, to_addr, links_subject, links_msg)
        except SendEmailError as e:
            self.logger.warning("Couldn't send links message")
            raise InternalError("Error while sending links message")

    def _send_help(self, locale, from_addr, to_addr):
        """Send help message.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and send the email.

        Params: locale - two-character string describing a locale.
                from_addr - address of the sender.
                to_addr - address of the recipient.

        """
        self.logger.debug("Request for help in %s" % locale)

        # Obtain the content in the proper language and send it
        t = gettext.translation(locale, './i18n', languages=[locale])
        _ = t.ugettext

        help_subject = _('help_subject')
        help_msg = _('help_msg')

        try:
            self._send_email(from_addr, to_addr, help_subject, help_msg)
        except SendEmailError as e:
            self.logger.warning("Couldn't send help message")
            raise InternalError("Error while sending help message")

    def _send_unsupported_os(self, operating_system, locale, from_addr,
                             to_addr):
        """Send unsupported OS message.

        Get the message for unsupported OS in the proper language
        (according to the locale, or in english if the locale is
        unsupported too), replace variables (if any) and send the email.

        Params: locale - two-character string describing a locale.
                from_addr - address of the sender.
                to_addr - address of the recipient.

        """
        # Check if the locale is unsupported too
        # If so, english by default
        supported_locales = self.core.get_supported_locales()
        if locale not in supported_locales:
            locale = 'en'

        # Obtain the content in the proper language and send it
        t = gettext.translation(locale, './i18n', languages=[locale])
        _ = t.ugettext

        unsupported_os_subject = _('unsupported_os_subject')
        unsupported_os_msg = _('unsupported_os_msg')
        unsupported_os_msg = unsupported_os_msg % operating_system

        try:
            self._send_email(from_addr, to_addr, unsupported_os_subject,
                             unsupported_os_msg)
        except SendEmailError as e:
            self.logger.warning("Couldn't send unsupported OS message")
            raise InternalError("Error while sending unsupported OS message")

    def _send_unsupported_locale(self, locale, operating_system, from_addr,
                                 to_addr):
        """Send unsupported locale message.

        Get the message for unsupported locale in english replace variables
        (if any) and send the email.

        Params: operating_system - name of the operating system.
                from_addr - address of the sender.
                to_addr - address of the recipient.

        """

        # Obtain the content in english and send it
        t = gettext.translation(locale, './i18n', languages=['en'])
        _ = t.ugettext

        unsupported_locale_subject = _('unsupported_locale_subject')
        unsupported_locale_msg = _('unsupported_locale_msg')
        unsupported_locale_msg = unsupported_locale_msg % locale

        try:
            self._send_email(from_addr, to_addr, unsupported_locale_subject,
                             unsupported_locale_msg)
        except SendEmailError as e:
            self.logger.warning("Couldn't send unsupported locale message")
            raise InternalError("Error while sending unsupported locale"
                                "message")

    def process_email(self, raw_msg):
        """Process the email received.

        Create an email object from the string received. The processing
        flow is as following:

            - Check for blacklisted address.
            - Parse the email.
            - Check the type of request.
            - Send reply.

        Raises: InternalError if something goes wrong while asking for the
                links to the Core module.

        Params: raw_msg - the email received.

        """
        parsed_msg = email.message_from_string(raw_msg)
        from_addr = parsed_msg['From']
        to_addr = parsed_msg['To']
        bogus_request = False

        try:
            norm_from_addr = self._get_normalized_address(from_addr)
        except AddressError as e:
            # This shouldn't stop us from receiving other requests
            self.logger.warning(str(e))
            bogus_request = True

        if norm_from_addr:
            try:
                self._check_blacklist(self._get_sha1(norm_from_addr))
            except BlacklistError as e:
                # This shouldn't stop us from receiving other requests
                self.logger.warning(str(e))
                bogus_request = True

        if not bogus_request:
            # Try to figure out what the user is asking
            request = self._parse_email(raw_msg, to_addr)

            # Two possible options: asking for help or for the links
            self.logger.info("New request for %s" % request['type'])
            if request['type'] == 'help':
                # make sure we can send emails
                try:
                    self._send_help(request['locale'], self.our_addr,
                                    norm_from_addr)
                except SendEmailError as e:
                    raise InternalError("Something's wrong with the SMTP "
                                        "server: %s" % str(e))

            elif request['type'] == 'links':
                if self.delay:
                    # make sure we can send emails
                    try:
                        self._send_delay(request['locale'], self.our_addr,
                                         norm_from_addr)
                    except SendEmailError as e:
                        raise InternalError("Something's wrong with the SMTP "
                                            "server: %s" % str(e))

                try:
                    self.logger.info("Asking core for links in %s for %s" %
                                     (request['locale'], request['os']))

                    links = self.core.get_links('SMTP', request['os'],
                                                request['locale'])

                except UnsupportedOSError as e:
                    self.logger.info("Request for unsupported OS: %s (%s)" %
                                     (request['os'], str(e)))
                    # if we got here, the address of the sender should be valid
                    # so we send him/her a message about the unsupported OS
                    self._send_unsupported_os(request['os'], request['locale'],
                                              self.our_addr, norm_from_addr)

                except UnsupportedLocaleError as e:
                    self.logger.info("Request for unsupported locale: %s (%s)"
                                     % (request['locale'], str(e)))
                    # if we got here, the address of the sender should be valid
                    # so we send him/her a message about the unsupported locale
                    self._send_unsupported_locale(request['locale'],
                                                  request['os'], self.our_addr,
                                                  norm_from_addr)

                # if core fails, we fail too
                except (InternalError, ConfigurationError) as e:
                    self.logger.error("Something's wrong with the Core module:"
                                      " %s" % str(e))
                    raise InternalError("Error obtaining the links.")

                # make sure we can send emails
                try:
                    self._send_links(links, request['locale'], request['os'],
                                     self.our_addr, norm_from_addr)
                except SendEmailError as e:
                    raise SendEmailError("Something's wrong with the SMTP "
                                         "server: %s" % str(e))
