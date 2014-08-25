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
import inspect
import logging
import tempfile
import ConfigParser

import db
import utils

"""Core module for getting links from providers."""


class ConfigurationError(Exception):
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
        ConfigurationError: Something's misconfigured.
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
            dbname = config.get('general', 'db')
            dbname = os.path.join(self.basedir, dbname)
            self.db = db.DB(dbname)
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'db' from 'general' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.linksdir = config.get('links', 'dir')
            self.linksdir = os.path.join(self.basedir, self.linksdir)
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'links' from 'dir' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.supported_lc = config.get('links', 'locales')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'locales' from 'links' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.supported_os = config.get('links', 'os')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'os' from 'links' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.loglevel = config.get('log', 'level')
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'level' from 'log' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.logdir = config.get('log', 'dir')
            self.logdir = os.path.join(self.basedir, self.logdir)
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'dir' from 'log' %s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        # keep log levels separated
        self.log = utils.filter_logging(logger, self.logdir, self.loglevel)
        # self.log.setLevel(logging.getLevelName(self.loglevel))
        self.log.info('Redirecting logging to %s' % self.logdir)

        # stop logging on stdout from now on
        self.log.propagate = False
        self.log.debug("New core object created")

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

        # Which module called us and what was asking for?
        self.log.info("%s did a request for %s, %s." % (service, os, lc))

        if lc not in self.supported_lc:
            self.log.warning("Request for unsupported locale: %s" % lc)
            raise UnsupportedLocaleError("Locale %s not supported" % lc)

        if os not in self.supported_os:
            self.log.warning("Request for unsupported OS: %s" % os)
            raise UnsupportedOSError("OS %s not supported " % os)

        # this could change in the future, let's leave it isolated.
        links = self._get_links(os, lc)

        if links is None:
            self.log.error("Couldn't get the links", exc_info=True)
            raise InternalError("Something went wrong internally. See logs for"
                                " detailed info.")

        self.log.info("Returning the links")
        return links

    def _get_links(self, os, lc):
        """Internal method to get the links.

        Looks for the links inside each provider file. This should only be
        called from get_links() method.

        :param: os (string) the operating system.
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

        self.log.info("Reading links from providers directory")
        for name in links:
            self.log.debug("Reading %s" % name)
            # We're reading files listed on linksdir, so they must exist!
            config = ConfigParser.ConfigParser()
            config.read(name)

            try:
                pname = config.get('provider', 'name')
            except ConfigParser.Error as e:
                self.log.warning("Couldn't get 'name' from 'provider' (%s)"
                                 % name)
                raise InternalError("Error while reading %s links file. See "
                                    "log file" % name)

            self.log.debug("Checking if %s has links for %s in %s" %
                           (pname, os, lc))

            try:
                providers[pname] = config.get(os, lc)
            except ConfigParser.Error as e:
                self.log.warning("Couldn't get %s from %s (%s)" %
                                 (lc, os, name))
                raise InternalError("Error while reading %s links file. See "
                                    "log file" % name)

            # each provider must have a fingerprint of the key used to
            # sign the uploaded packages
            try:
                self.log.debug("Trying to get fingerprint from %s", pname)
                fingerprint = config.get('key', 'fingerprint')
                providers[pname] = providers[pname] + "\nFingerprint: "
                providers[pname] = providers[pname] + fingerprint
                self.log.debug("Fingerprint added %s", fingerprint)
            except ConfigParser.Error as e:
                self.log.warning("Couldn't get 'fingerprint' from 'key' "
                                 "(%s)" % name)
                raise InternalError("Error while reading %s links file. See "
                                    "log file" % name)

        # create the final links list with all providers
        all_links = []

        self.log.debug("Joining all links found for %s in %s" % (os, lc))
        for key in providers.keys():
            all_links.append(
                "\n%s\n%s\n" % (key, ''.join(providers[key]))
            )

        if all_links:
            return "".join(all_links)
        else:
            self.log.warning("Trying to get supported os and locales, but"
                             " no links were found")
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
        self.log.info("Request to create new %s" % linksfile)

        if os.path.isfile(linksfile):
            # backup the old file in case something fails
            linksfile_backup = linksfile + '.backup'
            self.log.info("Backing up %s (%s)" % (linksfile, linksfile_backup))
            os.rename(linksfile, linksfile_backup)

        try:
            # this creates an empty links file (with no links)
            content = ConfigParser.RawConfigParser()
            content.add_section('provider')
            content.set('provider', 'name', provider)
            content.add_section('key')
            content.set('key', 'fingerprint', fingerprint)
            for os in self.supported_os:
                content.add_section(os)
            with open(linksfile, 'w+') as f:
                content.write(f)
                self.log.info("New %s created" % linksfile)
        except Exception as e:
            if linksfile_backup:
                os.rename(linksfile_backup, linksfile)
            raise LinkFileError("Error while trying to create new links file.")

    def add_link(self, provider, os, lc, link):
        """Public method to add a link to a provider's links file.

        Use ConfigParser to add a link into the os section, under the lc
        option. It checks for valid format; the provider's script should
        use the right format (see design).

        :param: provider (string) the provider.
        :param: os (string) the operating system.
        :param: lc (string) the locale.
        :param: link (string) link to be added. The format should be as
                follows:

                https://pkg_url https://asc_url

                where pkg_url is the url for the bundle and asc_url is the
                url for the asc of the bundle.

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
            self.log.warning("Can't add link for unsupported lc: %s" % lc)
            raise UnsupportedLocaleError("Locale %s not supported" % lc)

        if os not in self.supported_os:
            self.log.warning("Can't add link for unsupported os: %s" % os)
            raise UnsupportedOSError("OS %s not supported" % os)

        # check if the link has a legit format
        # e.g. https://db.tt/JjfUTb04 https://db.tt/MEfUTb04
        p = re.compile('^https://.+\shttps://.+$')

        if not p.match(link):
            self.log.warning("Can't add an invalid link: %s" % link)
            raise LinkFormatError("Link '%s' doesn't seem legit" % link)

        if os.path.isfile(linksfile):
            content = ConfigParser.RawConfigParser()
            content.readfp(open(linksfile))
            # check if exists and entry for locale; if not, create it
            try:
                links = content.get(os, lc)
                links = links + ",\n" + link
                content.set(oc, lc, links)
                with open(linksfile, 'w') as f:
                    content.write(f)
                self.log.info("Link %s added to %s %s in %s" %
                              (link, os, lc, provider))
            except ConfigParser.NoOptionError:
                content.set(os, lc, link)
                with open(linksfile, 'w') as f:
                    content.write(f)
                self.log.info("Link %s added to %s-%s in %s" %
                              (link, os, lc, provider))
            except ConfigParser.NoSectionError:
                # this shouldn't happen, but just in case
                self.log.error("Unknown section %s in links file")
                raise InternalError("Unknown %s section in links file" % os)
        else:
            raise LinkFileError("There is no links file for %s" % provider)

    def add_request_to_db(self, service, type, os, lc, pt, status, logfile):
        """Add request to database.

        This is for keeping stats about what is the most, less requested
        and stuff like that. Hopefully it will help to improve user experience.

        :param: type (string) the type of the request.
        :param: os (string) the operating system.
        :param: lc (string) the locale.
        :param: pt (bool) true if the user asked about pt, false otherwise.
        :param: status (string) short text describing the status.
        :param: logfile (string) path of the logfile of the email in case
                something went really wrong (address blacklisted/malformed).

        """
        self.db.add_request(service, type, os, lc, pt, status, logfile)
