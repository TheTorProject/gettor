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
import email
import gettext
import logging
import smtplib
import datetime
import ConfigParser

from email.mime.text import MIMEText

import core
import utils
import blacklist

"""SMTP module for processing email requests."""


class ConfigurationError(Exception):
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
        AddressError: Address of the sender malformed.
        SendEmailError: SMTP server not responding.
        InternalError: Something went wrong internally.

    """

    def __init__(self, cfg=None):
    	"""Create new object by reading a configuration file.

        :param: cfg (string) path of the configuration file.

        """
        # define a set of default values
        DEFAULT_CONFIG_FILE = 'smtp.cfg'

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
            self.basedir = config.get('general', 'basedir')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'basedir' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.our_domain = config.get('general', 'our_domain')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'our_domain' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            core_cfg = config.get('general', 'core_cfg')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'core_cfg' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            blacklist_cfg = config.get('blacklist', 'cfg')
            self.bl = blacklist.Blacklist(blacklist_cfg)
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
            self.logdir_emails = config.get('log', 'emails_dir')
            self.logdir_emails = os.path.join(self.logdir, self.logdir_emails)
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'emails_dir' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.loglevel = config.get('log', 'level')
        except ConfigParser.Error as e:
            log.warning("Couldn't read 'level' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        # use default values
        self.core = core.Core(core_cfg)

        # keep log levels separated
        self.log = utils.filter_logging(log, self.logdir, self.loglevel)
        self.log.setLevel(logging.getLevelName(self.loglevel))
        log.debug('Redirecting logging to %s' % self.logdir)

        # stop logging on stdout from now on
        log.propagate = False
        self.log.debug("New smtp object created")

    def _log_email(self, addr, content):
        """Log a request.

        This should be called when something goes wrong. It saves the
        email content that triggered the malfunctioning.

        :param: addr (string) the address of the sender.
        :param: content (string) the content of the email received.

        :return: (string) the path of the logfile of the email.
        """
        # we store the sha256 of the original address in order to know when
        # specific addresses are doing weird requests
        filename = "%s.log" % str(time.time())
        path = os.path.join(self.logdir_emails, filename)
        abs_path = os.path.abspath(path)

        log_file = open(abs_path, 'w+')
        log_file.write("Address: %s " % addr)
        log_file.write("\nBody:\n%s" % content)
        log_file.close()
        self.log.debug("Logging request from %s in %s" % (addr, abs_path))

        return filename

    def _is_blacklisted(self, addr):
        """Check if a user is blacklisted.

        :param: addr (string) the hashed address of the user.

        :return: true is the address is blacklisted, false otherwise.

        """
        self.log.debug("Checking if address %s is blacklisted" % addr)

        try:
            self.bl.is_blacklisted(addr, 'SMTP', self.bl_max_req,
                                   self.bl_wait_time)
            return False
        except blacklist.BlacklistError as e:
            self.log.info("Blacklisted address %s. Reason: %s" % (addr, e))
            return True

    def _get_lc(self, addr):
        """Get the locale from an email address.

        Process the email received and look for the locale in the recipient
        address (e.g. gettor+en@torproject.org). If no locale found, english
        by default.

        :param: (string) the email address we want to get the locale from.

        :return: (string) the locale (english if none).

        """
        self.log.debug("Trying to obtain locale from recipient address")

        # if no match found, english by default
        lc = 'en'

        # look for gettor+locale@torproject.org
        m = re.match('gettor\+(\w\w)@\w+\.\w+', addr)
        if m:
            self.log.debug("Request for locale %s" % m.groups())
            lc = "%s" % m.groups()

        return lc.lower()

    def _get_normalized_address(self, addr):
        """Get normalized address.

        We look for anything inside the last '<' and '>'. Code taken from
        the old GetTor (utils.py).

        :param: addr (string) the address we want to normalize.

        :raise: AddressError if the address can't be normalized.

        :return: (string) the normalized address.

        """
        if '<' in addr:
            idx = addr.rindex('<')
            addr = addr[idx:]
            m = re.search(r'<([^>]*)>', addr)
            if m is None:
                self.log.info("Malformed address: %s" % addr)
                raise AddressError("Couldn't extract normalized address "
                                   "from %s" % self_get_sha256(addr))
            addr = m.group(1)
        return addr

    def _get_content(self, email):
        """Get the body content of an email.

        :param: email (object) the email object to extract the content from.

        :return: (string) body of the message.

        """
        self.log.debug("Getting the body content of the email")
        maintype = email.get_content_maintype()
        if maintype == 'multipart':
            for part in email.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
        elif maintype == 'text':
            return email.get_payload()

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

    def _parse_email(self, msg, addr):
        """Parse the email received.

        Get the locale and parse the text for the rest of the info.

        :param: msg (string) the content of the email to be parsed.
        :param: addr (string) the address of the recipient (i.e. us).

        :return: (list) 4-tuple with locale, os and type of request.

        """
        self.log.debug("Parsing email")

        req = self._parse_text(msg)
        lc = self._get_lc(addr)
        req['lc'] = lc

        return req

    def _parse_text(self, msg):
        """Parse the text part of the email received.

        Try to figure out what the user is asking, namely, the type
        of request, the package and os required (if applies).

        :param: msg (string) the content of the email to be parsed.

        :return: (list) 3-tuple with the type of request, os and pt info.

        """
        self.log.debug("Parsing email text part")

        # by default we asume the request is asking for help
        req = {}
        req['type'] = 'help'
        req['os'] = None
        req['pt'] = False

        # core knows what OS are supported
        supported_os = self.core.get_supported_os()

        # we must search word by word, otherwise we could misinterpret
        # stuff (i.e. 'option' will match .*pt.*)
        found_os = False
        found_help = False
        lines = msg.split(' ')
        for word in lines:
            # check for help request
            if not found_os and re.match('help', word, re.IGNORECASE):
                self.log.info("Request for help found")
                req['type'] = 'help'
                found_help = True
                break
            # check for os
            if not found_os and not found_help:
                for os in supported_os:
                    if re.match(os, word, re.IGNORECASE):
                        req['os'] = os
                        req['type'] = 'links'
                        self.log.debug("Request for links found")
                        found_os = True
                        break
            # check if the user is asking for terms related to pt
            if re.match(".*obfs.*|pluggable|transport|pt",
                        word, re.IGNORECASE):
                self.log.info("Request for PT found")
                req['pt'] = True

        return req

    def _create_email(self, from_addr, to_addr, subject, msg):
        """Create an email object.

        This object will be used to construct the reply.

        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.
        :param: subject (string) the subject of the email.
        :param: msg (string) the content of the email.

        :return: (object) the email object.

        """
        self.log.debug("Creating email object for replying")
        email_obj = MIMEText(msg)
        email_obj.set_charset("utf-8")
        email_obj['Subject'] = subject
        email_obj['From'] = from_addr
        email_obj['To'] = to_addr

        return email_obj

    def _send_email(self, from_addr, to_addr, subject, msg):
        """Send an email.

        Take a 'from' and 'to' addresses, a subject and the content, creates
        the email and send it.

        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.
        :param: subject (string) the subject of the email.
        :param: msg (string) the content of the email.

        """
        email_obj = self._create_email(from_addr, to_addr, subject, msg)

        try:
            s = smtplib.SMTP("localhost")
            s.sendmail(from_addr, to_addr, email_obj.as_string())
            s.quit()
        except smtplib.SMTPException as e:
            self.log.error("Couldn't send the email: %s" % str(e))
            raise SendEmailError("Error with SMTP: %s" % str(e))

        self.log.debug("Email sent")

    def _send_links(self, links, lc, os, from_addr, to_addr, pt):
        """Send links to the user.

        Get the message in the proper language (according to the locale),
        replace variables and send the email.

        :param: links (string) the links to be sent.
        :param: lc (string) the locale.
        :param: os (string) the operating system.
        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.
        :param: pt (bool) true if the used asked for PT info; false otherwise.

        """
        self.log.debug("Request for links in %s" % lc)

        # obtain the content in the proper language and send it
        links_subject = self._get_msg('links_subject', lc)
        links_msg = self._get_msg('links_msg', lc)
        links_msg = links_msg % (os, lc, links)

        # don't forget to check if user did a PT request
        if pt:
            # if so, we get the links message + info about PT included.
            links_subject = self._get_msg('links_pt_subject', lc)
            links_msg = self._get_msg('links_pt_msg', lc)
            links_msg = links_msg % (os, lc, links)

        try:
            self._send_email(from_addr, to_addr, links_subject, links_msg)
        except SendEmailError as e:
            self.log.warning("Couldn't send links message")
            raise InternalError("Error while sending links message")

    def _send_help(self, lc, from_addr, to_addr):
        """Send help message.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and send the email.

        :param: lc (string) the locale.
        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.

        """
        self.log.debug("Request for help in %s" % lc)

        # obtain the content in the proper language and send it
        help_subject = self._get_msg('help_subject', lc)
        help_msg = self._get_msg('help_msg', lc)

        try:
            self._send_email(from_addr, to_addr, help_subject, help_msg)
        except SendEmailError as e:
            self.log.warning("Couldn't send help message")
            raise InternalError("Error while sending help message")

    def _send_unsupported_lc(self, lc, os, from_addr, to_addr):
        """Send unsupported locale message.

        Get the message for unsupported locale in english replace variables
        (if any) and send the email.

        :param: lc (string) the locale.
        :param: os (string) the operating system.
        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.

        """

        # obtain the content in english and send it
        unsupported_lc_subject = self._get_msg('unsupported_lc_subject', 'en')
        unsupported_lc_msg = self._get_msg('unsupported_lc_msg', 'en')
        unsupported_lc_msg = unsupported_lc_msg % lc

        try:
            self._send_email(from_addr, to_addr, unsupported_lc_subject,
                             unsupported_lc_msg)

        except SendEmailError as e:
            self.log.warning("Couldn't send unsupported locale message")
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

        :param: raw_msg (string) the email received.

        :raise: InternalError if something goes wrong while asking for the
                links to the Core module.

        """
        parsed_msg = email.message_from_string(raw_msg)
        content = self._get_content(parsed_msg)
        from_addr = parsed_msg['From']
        to_addr = parsed_msg['To']
        bogus_request = False
        logfile = ''
        status = ''
        req = None

        try:
            # two ways for a request to be bogus: address malformed or
            # blacklisted
            try:
                norm_from_addr = self._get_normalized_address(from_addr)
            except AddressError as e:
                status = 'malformed'
                bogus_request = True
                # it might be interesting to know what triggered this
                logfile = self._log_email('malformed', content)

            if norm_from_addr:
                anon_addr = utils.get_sha256(norm_from_addr)

                if self._is_blacklisted(anon_addr):
                    status = 'blacklisted'
                    bogus_request = True
                    # it might be interesting to know extra info
                    logfile = self._log_email(anon_addr, content)

            if not bogus_request:
                # try to figure out what the user is asking
                req = self._parse_email(content, to_addr)

                # our address should have the locale requested
                our_addr = "gettor+%s@%s" % (req['lc'], self.our_domain)

                # two possible options: asking for help or for the links
                self.log.info("New request for %s" % req['type'])
                if req['type'] == 'help':
                    # make sure we can send emails
                    try:
                        self._send_help(req['lc'], our_addr, norm_from_addr)
                    except SendEmailError as e:
                        status = 'internal_error'
                        raise InternalError("Something's wrong with the SMTP "
                                            "server: %s" % str(e))

                elif req['type'] == 'links':
                    try:
                        self.log.info("Asking core for links in %s for %s" %
                                      (req['lc'], req['os']))

                        links = self.core.get_links('SMTP', req['os'],
                                                    req['lc'])

                    except core.UnsupportedLocaleError as e:
                        self.log.info("Request for unsupported locale: %s (%s)"
                                      % (req['lc'], str(e)))
                        # if we got here, the address of the sender should
                        # be valid so we send him/her a message about the
                        # unsupported locale
                        status = 'unsupported_lc'
                        self._send_unsupported_lc(req['lc'], req['os'],
                                                  our_addr, norm_from_addr)
                        return

                    # if core fails, we fail too
                    except (core.InternalError, core.ConfigurationError) as e:
                        status = 'core_error'
                        self.log.error("Something went wrong with Core: %s"
                                       % str(e))
                        raise InternalError("Error obtaining the links.")

                    # make sure we can send emails
                    try:
                        self._send_links(links, req['lc'], req['os'], our_addr,
                                         norm_from_addr, req['pt'])
                    except SendEmailError as e:
                        status = 'internal_error'
                        raise SendEmailError("Something's wrong with the SMTP "
                                             "server: %s" % str(e))
                status = 'success'
        finally:
            # keep stats
            if req:
                self.core.add_request_to_db('SMTP',
                                            req['type'], req['os'],
                                            req['lc'], req['pt'],
                                            status, logfile)
            else:
                # invalid request, so no info about it
                # logfiles were created for this
                self.core.add_request_to_db('SMTP', '', '', '', '',
                                            status, logfile)
