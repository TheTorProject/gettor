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
import email
import gettext
import logging
import smtplib
import datetime
import ConfigParser

from email import Encoders
from email.MIMEBase import MIMEBase
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart

import core
import utils
import blacklist

"""SMTP module for processing email requests."""

OS = {
    'osx': 'Mac OS X',
    'linux': 'Linux',
    'windows': 'Windows'
}


class ConfigError(Exception):
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

        ConfigError: Bad configuration.
        AddressError: Address of the sender malformed.
        SendEmailError: SMTP server not responding.
        InternalError: Something went wrong internally.

    """

    def __init__(self, cfg=None):
    	"""Create new object by reading a configuration file.

        :param: cfg (string) path of the configuration file.

        """
        default_cfg = 'smtp.cfg'
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = default_cfg

        try:
            with open(cfg) as f:
                config.readfp(f)
        except IOError:
            raise ConfigError("File %s not found!" % cfg)

        try:
            self.our_domain = config.get('general', 'our_domain')
            self.mirrors = config.get('general', 'mirrors')
            self.i18ndir = config.get('i18n', 'dir')

            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'smtp.log')
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

    def _is_blacklisted(self, addr):
        """Check if a user is blacklisted.

        :param: addr (string) the hashed address of the user.

        :return: true is the address is blacklisted, false otherwise.

        """

        try:
            self.bl.is_blacklisted(
                addr, 'SMTP', self.bl_max_req, self.bl_wait_time
            )
            return False
        except blacklist.BlacklistError as e:
            return True

    def _get_lc(self, addr):
        """Get the locale from an email address.

        Process the email received and look for the locale in the recipient
        address (e.g. gettor+en@torproject.org). If no locale found, english
        by default.

        :param: (string) the email address we want to get the locale from.

        :return: (string) the locale (english if none).

        """
        # if no match found, english by default
        lc = 'en'

        # look for gettor+locale@torproject.org
        m = re.match('gettor\+(\w\w)@\w+\.\w+', addr)
        if m:
            # we found a request for locale lc
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
                # malformed address
                raise AddressError("Couldn't extract normalized address "
                                   "from %s" % self_get_sha256(addr))
            addr = m.group(1)
        return addr

    def _get_content(self, email):
        """Get the body content of an email.

        :param: email (object) the email object to extract the content from.

        :return: (string) body of the message.

        """
        # get the body content of the email
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
        # obtain the content in the proper language
        try:
            t = gettext.translation(lc, self.i18ndir, languages=[lc])
            _ = t.ugettext

            msgstr = _(msgid)
            return msgstr
        except IOError as e:
            raise ConfigError("%s" % str(e))

    def _parse_email(self, msg, addr):
        """Parse the email received.

        Get the locale and parse the text for the rest of the info.

        :param: msg (string) the content of the email to be parsed.
        :param: addr (string) the address of the recipient (i.e. us).

        :return: (list) 4-tuple with locale, os and type of request.

        """
        req = self._parse_text(msg)
        lc = self._get_lc(addr)
        supported_lc = self.core.get_supported_lc()

        if lc in supported_lc:
            req['lc'] = lc
        else:
            req['lc'] = 'en'

        return req

    def _parse_text(self, msg):
        """Parse the text part of the email received.

        Try to figure out what the user is asking, namely, the type
        of request, the package and os required (if applies).

        :param: msg (string) the content of the email to be parsed.

        :return: (list) 3-tuple with the type of request, os and pt info.

        """
        # by default we asume the request is asking for help
        req = {}
        req['type'] = 'help'
        req['os'] = None

        # core knows what OS are supported
        supported_os = self.core.get_supported_os()

        # search for OS or mirrors request
        # if nothing is found, help by default
        found_request = False
        words = re.split('\s+', msg.strip())
        for word in words:
            if not found_request:
                # OS first
                for os in supported_os:
                    if re.match(os, word, re.IGNORECASE):
                        req['os'] = os
                        req['type'] = 'links'
                        found_request = True
                        break
                # mirrors
                if re.match("mirrors?", word, re.IGNORECASE):
                    req['type'] = 'mirrors'
                    found_request = True
            else:
                break
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
        email_obj = MIMEMultipart()
        email_obj.set_charset("utf-8")
        email_obj['Subject'] = subject
        email_obj['From'] = from_addr
        email_obj['To'] = to_addr

        msg_attach = MIMEText(msg, 'plain')
        email_obj.attach(msg_attach)

        return email_obj

    def _send_email(self, from_addr, to_addr, subject, msg, attach=None):
        """Send an email.

        Take a 'from' and 'to' addresses, a subject and the content, creates
        the email and send it.

        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.
        :param: subject (string) the subject of the email.
        :param: msg (string) the content of the email.
        :param: attach (string) the path of the mirrors list.

        """
        email_obj = self._create_email(from_addr, to_addr, subject, msg)

        if(attach):
            # for now, the only email with attachment is the one for mirrors
            try:
                part = MIMEBase('application', "octet-stream")
                part.set_payload(open(attach, "rb").read())
                Encoders.encode_base64(part)

                part.add_header(
                    'Content-Disposition',
                    'attachment; filename="mirrors.txt"'
                )

                email_obj.attach(part)
            except IOError as e:
                raise SendEmailError('Error with mirrors: %s' % str(e))

        try:
            s = smtplib.SMTP("localhost")
            s.sendmail(from_addr, to_addr, email_obj.as_string())
            s.quit()
        except smtplib.SMTPException as e:
            raise SendEmailError("Error with SMTP: %s" % str(e))

    def _send_links(self, links, lc, os, from_addr, to_addr):
        """Send links to the user.

        Get the message in the proper language (according to the locale),
        replace variables and send the email.

        :param: links (string) the links to be sent.
        :param: lc (string) the locale.
        :param: os (string) the operating system.
        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.

        """
        # obtain the content in the proper language and send it
        try:
            links_subject = self._get_msg('links_subject', 'en')
            links_msg = self._get_msg('links_msg', 'en')
            links_msg = links_msg % (OS[os], links)

            self._send_email(
                from_addr,
                to_addr,
                links_subject,
                links_msg,
                None
            )
        except ConfigError as e:
            raise InternalError("Error while getting message %s" % str(e))
        except SendEmailError as e:
            raise InternalError("Error while sending links message")

    def _send_mirrors(self, lc, from_addr, to_addr):
        """Send mirrors message.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and send the email.

        :param: lc (string) the locale.
        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.

        """
        # obtain the content in the proper language and send it
        try:
            mirrors_subject = self._get_msg('mirrors_subject', lc)
            mirrors_msg = self._get_msg('mirrors_msg', lc)

            self._send_email(
                from_addr, to_addr, mirrors_subject, mirrors_msg, self.mirrors
            )
        except ConfigError as e:
            raise InternalError("Error while getting message %s" % str(e))
        except SendEmailError as e:
            raise InternalError("Error while sending mirrors message")

    def _send_help(self, lc, from_addr, to_addr):
        """Send help message.

        Get the message in the proper language (according to the locale),
        replace variables (if any) and send the email.

        :param: lc (string) the locale.
        :param: from_addr (string) the address of the sender.
        :param: to_addr (string) the address of the recipient.

        """
        # obtain the content in the proper language and send it
        try:
            help_subject = self._get_msg('help_subject', lc)
            help_msg = self._get_msg('help_msg', lc)

            self._send_email(from_addr, to_addr, help_subject, help_msg, None)
        except ConfigError as e:
            raise InternalError("Error while getting message %s" % str(e))
        except SendEmailError as e:
            raise InternalError("Error while sending help message")

    def process_email(self, raw_msg):
        """Process the email received.

        Create an email object from the string received. The processing
        flow is as following:

            - check for blacklisted address.
            - parse the email.
            - check the type of request.
            - send reply.

        :param: raw_msg (string) the email received.

        :raise: InternalError if something goes wrong while asking for the
                links to the Core module.

        """
        self.log.debug("Processing email")
        parsed_msg = email.message_from_string(raw_msg)
        content = self._get_content(parsed_msg)
        from_addr = parsed_msg['From']
        to_addr = parsed_msg['To']
        bogus_request = False
        status = ''
        req = None

        try:
            # two ways for a request to be bogus: address malformed or
            # blacklisted
            try:
                self.log.debug("Normalizing address...")
                norm_from_addr = self._get_normalized_address(from_addr)
            except AddressError as e:
                bogus_request = True
                self.log.info('invalid; none; none')

            if norm_from_addr:
                anon_addr = utils.get_sha256(norm_from_addr)

                if self._is_blacklisted(anon_addr):
                    bogus_request = True
                    self.log.info('blacklist; none; none')

            if not bogus_request:
                # try to figure out what the user is asking
                self.log.debug("Request seems legit; parsing it...")
                req = self._parse_email(content, to_addr)

                # our address should have the locale requested
                our_addr = "gettor+%s@%s" % (req['lc'], self.our_domain)

                # possible options: help, links, mirrors
                if req['type'] == 'help':
                    self.log.debug("Trying to send help...")
                    self.log.info('help; none; %s' % req['lc'])
                    # make sure we can send emails
                    try:
                        self._send_help('en', our_addr, norm_from_addr)
                    except SendEmailError as e:
                        self.log.debug("FAILED: %s" % str(e))
                        raise InternalError("Something's wrong with the SMTP "
                                            "server: %s" % str(e))

                elif req['type'] == 'mirrors':
                    self.log.debug("Trying to send the mirrors...")
                    self.log.info('mirrors; none; %s' % req['lc'])
                    # make sure we can send emails
                    try:
                        self._send_mirrors('en', our_addr, norm_from_addr)
                    except SendEmailError as e:
                        self.log.debug("FAILED: %s" % str(e))
                        raise SendEmailError("Something's wrong with the SMTP "
                                             "server: %s" % str(e))

                elif req['type'] == 'links':
                    self.log.debug("Trying to obtain the links...")
                    self.log.info('links; %s; %s' % (req['os'], req['lc']))

                    try:
                        links = self.core.get_links(
                            'SMTP', req['os'], req['lc']
                        )
                    # if core fails, we fail too
                    except (core.InternalError, core.ConfigError) as e:
                        self.log.debug("FAILED: %s" % str(e))
                        # something went wrong with the core
                        raise InternalError("Error obtaining the links")

                    # make sure we can send emails
                    self.log.debug("Trying to send the links...")
                    try:
                        self._send_links(links, req['lc'], req['os'], our_addr,
                                         norm_from_addr)
                    except SendEmailError as e:
                        self.log.debug("FAILED: %s" % str(e))
                        raise SendEmailError("Something's wrong with the SMTP "
                                             "server: %s" % str(e))
        finally:
            self.log.debug("Request processed")
