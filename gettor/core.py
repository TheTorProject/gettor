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
import inspect
import logging
import tempfile
import ConfigParser

import db
import utils

"""Core module for getting links from providers."""


class ConfigError(Exception):
    pass


class UnsupportedOSError(Exception):
    pass


class UnsupportedLocaleError(Exception):
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

        UnsupportedOSError: Request for an unsupported operating system.
        UnsupportedLocaleError: Request for an unsupported locale.
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
        # define a set of default values
        DEFAULT_CONFIG_FILE = 'core.cfg'

        logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")
        log = logging.getLogger(__name__)
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = DEFAULT_CONFIG_FILE

        config.read(cfg)

        try:
            basedir = config.get('general', 'basedir')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'basedir' from 'general'")

        try:
            dbname = config.get('general', 'db')
            dbname = os.path.join(basedir, dbname)
            self.db = db.DB(dbname)
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'db' from 'general'")

        try:
            self.linksdir = config.get('links', 'dir')
            self.linksdir = os.path.join(basedir, self.linksdir)
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'links' from 'dir'")

        try:
            self.supported_lc = config.get('links', 'locales')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'locales' from 'links'")

        try:
            self.supported_os = config.get('links', 'os')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'os' from 'links'")

        try:
            loglevel = config.get('log', 'level')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'level' from 'log'")

        try:
            logdir = config.get('log', 'dir')
            logfile = os.path.join(logdir, 'core.log')
        except ConfigParser.Error as e:
            raise ConfigError("Couldn't read 'dir' from 'log'")

        # establish log level and redirect to log file
        log.info('Redirecting logging to %s' % logfile)
        logfileh = logging.FileHandler(logfile, mode='a+')
        logfileh.setLevel(logging.getLevelName(loglevel))
        log.addHandler(logfileh)

        # stop logging on stdout from now on
        log.propagate = False

    def get_links(self, service, os, lc):
        """Get links for OS in locale.

        This method should be called from the services modules of
        GetTor (e.g. SMTP). To make it easy we let the module calling us
        specify the name of the service (for stats purpose).

        :param: service (string) the service trying to get the links.
        :param: os (string) the operating system.
        :param: lc (string) tthe locale.

        :raise: UnsupportedOSError if the operating system is not supported.
        :raise: UnsupportedLocaleError if the locale is not supported.
        :raise: InternalError if something goes wrong while internally.

        :return: (string) the links.

        """

        if lc not in self.supported_lc:
            raise UnsupportedLocaleError("Locale %s not supported" % lc)

        if os not in self.supported_os:
            raise UnsupportedOSError("OS %s not supported " % os)

        # this could change in the future, let's leave it isolated.
        links = self._get_links(os, lc)

        if links is None:
            raise InternalError("Something went wrong internally")

        # thanks for stopping by
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
        links = []

        # look for files ending with .links
        p = re.compile('.*\.links$')

        for name in os.listdir(self.linksdir):
            path = os.path.abspath(os.path.join(self.linksdir, name))
            if os.path.isfile(path) and p.match(path):
                links.append(path)

        # let's create a dictionary linking each provider with the links
        # found for os and lc. This way makes it easy to check if no
        # links were found
        providers = {}

        # reading links from providers directory
        for name in links:
            # we're reading files listed on linksdir, so they must exist!
            config = ConfigParser.ConfigParser()
            config.read(name)

            try:
                pname = config.get('provider', 'name')
            except ConfigParser.Error as e:
                raise InternalError("Couldn't get 'name' from 'provider'")

            # checking if current provider pname has links for os in lc
            try:
                providers[pname] = config.get(osys, lc)
                # avoid showing it all together
                providers[pname] = providers[pname].replace(",", "\n")
            except ConfigParser.Error as e:
                raise InternalError("Couldn't get %s from %s (%s)" %
                                    (lc, osys, name))

            # each provider must have a fingerprint of the key used to
            # sign the uploaded packages
            try:
                fingerprint = config.get('key', 'fingerprint')
                providers[pname] = "%s\n\nFingerprint: %s" %\
                                   (providers[pname], fingerprint)
            except ConfigParser.Error as e:
                raise InternalError("Couldn't get 'fingerprint' from 'key'")

        # create the final links list with all providers
        all_links = []

        for key in providers.keys():
            all_links.append(
                "\n%s\n\n%s\n" % (key, ''.join(providers[key]))
            )

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

        if os.path.isfile(linksfile):
            # backup the old file in case something fails
            linksfile_backup = linksfile + '.backup'
            os.rename(linksfile, linksfile_backup)

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
            if linksfile_backup:
                os.rename(linksfile_backup, linksfile)
            raise LinkFileError("Error while creating new links file: %s" % e)

    def add_link(self, provider, osys, lc, link):
        """Public method to add a link to a provider's links file.

        Use ConfigParser to add a link into the os section, under the lc
        option. It checks for valid format; the provider's script should
        use the right format (see design).

        :param: provider (string) the provider.
        :param: os (string) the operating system.
        :param: lc (string) the locale.
        :param: link (string) link to be added.

        :raise: UnsupportedOSError if the operating system is not supported.
        :raise: UnsupportedLocaleError if the locale is not supported.
        :raise: LinkFileError if there is no links file for the provider.
        :raise: LinkFormatError if the link format doesn't seem legit.
        :raise: InternalError if the links file doesn't have a section for
                the OS requested. This *shouldn't* happen because it means
                the file wasn't created correctly.

        """
        linksfile = os.path.join(self.linksdir, provider.lower() + '.links')

        # don't try to add unsupported stuff
        if lc not in self.supported_lc:
            raise UnsupportedLocaleError("Locale %s not supported" % lc)

        if osys not in self.supported_os:
            raise UnsupportedOSError("OS %s not supported" % osys)

        if os.path.isfile(linksfile):
            content = ConfigParser.RawConfigParser()
            content.readfp(open(linksfile))
            # check if exists and entry for locale; if not, create it
            try:
                links = content.get(osys, lc)
                links = "%s,\n%s" % (links, link)
                content.set(osys, lc, links)
                with open(linksfile, 'w') as f:
                    content.write(f)
            except ConfigParser.NoOptionError:
                content.set(osys, lc, link)
                with open(linksfile, 'w') as f:
                    content.write(f)
            except ConfigParser.NoSectionError:
                # this shouldn't happen, but just in case
                raise InternalError("Unknown %s section in links file" % osys)
        else:
            raise LinkFileError("There is no links file for %s" % provider)

    def add_request_to_db(self):
        """Add request to database."""
        self.db.add_request()
