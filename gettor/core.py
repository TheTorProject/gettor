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
import logging
import gettext
import tempfile
import ConfigParser

import db
import utils

"""Core module for getting links from providers."""


class ConfigError(Exception):
    pass


class NotSupportedError(Exception):
    pass


class LinkFormatError(Exception):
    pass


class LinkFileError(Exception):
    pass


class InternalError(Exception):
    pass


class Core(object):
    """Get links from providers and deliver them to other modules.

    Public methods:

        get_links(): Get the links for the OS and locale requested.
        create_links_file(): Create a file to store links of a provider.
        add_link(): Add a link to a links file of a provider.
        get_supported_os(): Get a list of supported operating systems.
        get_supported_lc(): Get a list of supported locales.

    Exceptions:

        UnsupportedOSError: OS and/or locale not supported.
        ConfigError: Something's misconfigured.
        LinkFormatError: The link added doesn't seem legit.
        LinkFileError: Error related to the links file of a provider.
        InternalError: Something went wrong internally.

    """

    def __init__(self, cfg=None):
    	"""Create a new core object by reading a configuration file.

        :param: cfg (string) the path of the configuration file.
        :raise: ConfigurationError if the configuration file doesn't exists
                or if something goes wrong while reading options from it.

        """
        default_cfg = 'core.cfg'
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = default_cfg

        try:
            with open(cfg) as f:
                config.readfp(f)
        except IOError:
            raise ConfigError("File %s not found!" % cfg)

        try:
            self.supported_lc = config.get('links', 'locales')
            self.supported_os = config.get('links', 'os')

            basedir = config.get('general', 'basedir')
            self.linksdir = config.get('links', 'dir')
            self.linksdir = os.path.join(basedir, self.linksdir)
            self.i18ndir = config.get('i18n', 'dir')

            loglevel = config.get('log', 'level')
            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'core.log')

            dbname = config.get('general', 'db')
            dbname = os.path.join(basedir, dbname)
            self.db = db.DB(dbname)

        except ConfigParser.Error as e:
            raise ConfigError("Configuration error: %s" % str(e))
        except db.Exception as e:
            raise InternalError("%s" % e)

        # logging
        log = logging.getLogger(__name__)

        logging_format = utils.get_logging_format()
        date_format = utils.get_date_format()
        formatter = logging.Formatter(logging_format, date_format)

        log.info('Redirecting CORE logging to %s' % logfile)
        logfileh = logging.FileHandler(logfile, mode='a+')
        logfileh.setFormatter(formatter)
        logfileh.setLevel(logging.getLevelName(loglevel))
        log.addHandler(logfileh)

        # stop logging on stdout from now on
        log.propagate = False
        self.log = log

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

    def get_links(self, service, os, lc):
        """Get links for OS in locale.

        This method should be called from the services modules of
        GetTor (e.g. SMTP). To make it easy we let the module calling us
        specify the name of the service (for stats purpose).

        :param: service (string) the service trying to get the links.
        :param: os (string) the operating system.
        :param: lc (string) tthe locale.

        :raise: InternalError if something goes wrong while internally.

        :return: (string) the links.

        """
        # english and windows by default
        if lc not in self.supported_lc:
            self.log.debug("Request for locale not supported. Default to en")
            lc = 'en'

        if os not in self.supported_os:
            self.log.debug("Request for OS not supported. Default to windows")
            os = 'windows'

        # this could change in the future, let's leave it isolated.
        self.log.debug("Trying to get the links...")
        try:
            links = self._get_links(os, lc)
            self.log.debug("OK")
        except InternalError as e:
            self.log.debug("FAILED")
            raise InternalError("%s" % str(e))

        if links is None:
            self.log.debug("No links found")
            raise InternalError("No links. Something is wrong.")

        return links

    def _get_links(self, osys, lc):
        """Internal method to get the links.

        Looks for the links inside each provider file. This should only be
        called from get_links() method.

        :param: osys (string) the operating system.
        :param: lc (string) the locale.

        :return: (string/None) links on success, None otherwise.

        """

        # read the links files using ConfigParser
        # see the README for more details on the format used
        links_files = []
        
        links32 = {}
        links64 = {}
        
        # for the message to be sent
        if osys == 'windows':
            arch = '32/64'
        elif osys == 'osx':
            arch = '64'
        else:
            arch = '32'

        # look for files ending with .links
        p = re.compile('.*\.links$')

        for name in os.listdir(self.linksdir):
            path = os.path.abspath(os.path.join(self.linksdir, name))
            if os.path.isfile(path) and p.match(path):
                links_files.append(path)

        # let's create a dictionary linking each provider with the links
        # found for os and lc. This way makes it easy to check if no
        # links were found
        providers = {}

        # separator
        spt = '=' * 72

        # reading links from providers directory
        for name in links_files:
            # we're reading files listed on linksdir, so they must exist!
            config = ConfigParser.ConfigParser()
            # but just in case they don't
            try:
                with open(name) as f:
                    config.readfp(f)
            except IOError:
                raise InternalError("File %s not found!" % name)

            try:
                pname = config.get('provider', 'name')

                # check if current provider pname has links for os in lc
                providers[pname] = config.get(osys, lc)
            except ConfigParser.Error as e:
                # we should at least have the english locale available
                self.log.error("Request for %s, returning 'en' instead" % lc)
                providers[pname] = config.get(osys, 'en')
            try:
                #test = providers[pname].split("$")
                #self.log.debug(test)
                if osys == 'linux':
                    t32, t64 = [t for t in providers[pname].split(",") if t]
                    
                    link, signature, chs32 = [l for l in t32.split("$") if l]
                    links32[link] = signature

                    link, signature, chs64 = [l for l in t64.split("$") if l]
                    links64[link] = signature
                    
                else:
                    link, signature, chs32 = [l for l in providers[pname].split("$") if l]
                    links32[link] = signature
                    
                #providers[pname] = providers[pname].replace(",", "")
                #providers[pname] = providers[pname].replace("$", "\n\n")

                # all packages are signed with same key
                # (Tor Browser developers)
                fingerprint = config.get('key', 'fingerprint')
                # for now, english messages only
                fingerprint_msg = self._get_msg('fingerprint', 'en')
                fingerprint_msg = fingerprint_msg % fingerprint
            except ConfigParser.Error as e:
                raise InternalError("%s" % str(e))

        # create the final links list with all providers
        all_links = []

        msg = "Tor Browser %s-bit:" % arch
        for link in links32:
            msg = "%s\n%s" % (msg, link)
            
        all_links.append(msg)
        
        if osys == 'linux':
            msg = "\n\n\nTor Browser 64-bit:"
            for link in links64:
                msg = "%s\n%s" % (msg, link)
        
            all_links.append(msg)
        
        msg = "\n\n\nTor Browser's signature %s-bit (in the same order):" %\
              arch
        for link in links32:
            msg = "%s\n%s" % (msg, links32[link])
        
        all_links.append(msg)
        
        if osys == 'linux':
            msg = "\n\n\nTor Browser's signature 64-bit:"
            for link in links64:
                msg = "%s\n%s" % (msg, links64[link])
            
            all_links.append(msg)
        
        msg = "\n\n\nSHA256 of Tor Browser %s-bit (advanced): %s\n" %\
              (arch, chs32)
        all_links.append(msg)
        
        if osys == 'linux':
            msg = "SHA256 of Tor Browser 64-bit (advanced): %s\n" % chs64
            all_links.append(msg)

        """
        for key in providers.keys():
            # get more friendly description of the provider
            try:
                # for now, english messages only
                provider_desc = self._get_msg('provider_desc', 'en')
                provider_desc = provider_desc % key

                all_links.append(
                    "%s\n%s\n\n%s%s\n\n\n" %
                    (provider_desc, spt, ''.join(providers[key]), spt)
                )
            except ConfigError as e:
                raise InternalError("%s" % str(e))
        """

        # add fingerprint after the links
        all_links.append(fingerprint_msg)

        if all_links:
            return "".join(all_links)
        else:
            # we're trying to get supported os an lc
            # but there aren't any links!
            return None

    def get_supported_os(self):
        """Public method to get the list of supported operating systems.

        :return: (list) the supported operating systems.

        """
        return self.supported_os.split(',')

    def get_supported_lc(self):
        """Public method to get the list of supported locales.

        :return: (list) the supported locales.

        """
        return self.supported_lc.split(',')

    def create_links_file(self, provider, fingerprint):
        """Public method to create a links file for a provider.

        This should be used by all providers since it writes the links
        file with the proper format. It backs up the old links file
        (if exists) and creates a new one.

        :param: provider (string) the provider (links file will use this
                name in slower case).
        :param: fingerprint (string) the fingerprint of the key that signed
                the packages to be uploaded to the provider.

        """
        linksfile = os.path.join(self.linksdir, provider.lower() + '.links')
        linksfile_backup = ""

        self.log.debug("Request to create a new links file")
        if os.path.isfile(linksfile):
            self.log.debug("Trying to backup the old one...")
            try:
                # backup the old file in case something fails
                linksfile_backup = linksfile + '.backup'
                os.rename(linksfile, linksfile_backup)
            except OSError as e:
                self.log.debug("FAILED %s" % str(e))
                raise LinkFileError(
                    "Error while creating new links file: %s" % str(e)
                )

            self.log.debug("Creating empty links file...")
            try:
                # this creates an empty links file
                content = ConfigParser.RawConfigParser()
                content.add_section('provider')
                content.set('provider', 'name', provider)
                content.add_section('key')
                content.set('key', 'fingerprint', fingerprint)
                content.add_section('linux')
                content.add_section('windows')
                content.add_section('osx')
                with open(linksfile, 'w+') as f:
                    content.write(f)
            except Exception as e:
                self.log.debug("FAILED: %s" % str(e))
                # if we passed the last exception, then this shouldn't
                # be a problem...
                if linksfile_backup:
                    os.rename(linksfile_backup, linksfile)
                raise LinkFileError(
                    "Error while creating new links file: %s" % str(e)
                )

    def add_link(self, provider, osys, lc, link):
        """Public method to add a link to a provider's links file.

        Use ConfigParser to add a link into the os section, under the lc
        option. It checks for valid format; the provider's script should
        use the right format (see design).

        :param: provider (string) the provider.
        :param: os (string) the operating system.
        :param: lc (string) the locale.
        :param: link (string) link to be added.

        :raise: NotsupportedError if the OS and/or locale is not supported.
        :raise: LinkFileError if there is no links file for the provider.
        :raise: LinkFormatError if the link format doesn't seem legit.
        :raise: InternalError if the links file doesn't have a section for
                the OS requested. This *shouldn't* happen because it means
                the file wasn't created correctly.

        """
        linksfile = os.path.join(self.linksdir, provider.lower() + '.links')

        self.log.debug("Request to add a new link")
        # don't try to add unsupported stuff
        if lc not in self.supported_lc:
            self.log.debug("Request for locale %s not supported" % lc)
            raise NotSupportedError("Locale %s not supported" % lc)

        if osys not in self.supported_os:
            self.log.debug("Request for OS %s not supported" % osys)
            raise NotSupportedError("OS %s not supported" % osys)

        self.log.debug("Opening links file...")
        if os.path.isfile(linksfile):
            content = ConfigParser.RawConfigParser()

            try:
                with open(linksfile) as f:
                    content.readfp(f)
            except IOError as e:
                self.log.debug("FAILED %s" % str(e))
                raise LinksFileError("File %s not found!" % linksfile)
            # check if exists and entry for locale; if not, create it
            self.log.debug("Trying to add the link...")
            try:
                links = content.get(osys, lc)
                links = "%s,\n%s" % (links, link)
                content.set(osys, lc, links)
                self.log.debug("Link added")
                with open(linksfile, 'w') as f:
                    content.write(f)
            except ConfigParser.NoOptionError:
                content.set(osys, lc, link)
                self.log.debug("Link added (with new locale created)")
                with open(linksfile, 'w') as f:
                    content.write(f)
            except ConfigParser.NoSectionError as e:
                # this shouldn't happen, but just in case
                self.log.debug("FAILED (OS not found)")
                raise InternalError("Unknown section %s" % str(e))
        else:
            self.log.debug("FAILED (links file doesn't seem legit)")
            raise LinkFileError("No links file for %s" % provider)

    def add_request_to_db(self):
        """Add request to database."""
        self.log.debug("Trying to add request to database")
        try:
            self.db.connect()
            self.db.add_request()
            self.log.debug("Request added!")
        except db.DBError as e:
            self.log.debug("FAILED %s" % str(e))
            raise InternalError("Couldn't add request to database %s" % str(e))
