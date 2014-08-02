# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser Bundle distribution system.
#

import os
import re
import inspect
import logging
import tempfile
import ConfigParser

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
        get_supported_locale(): Get a list of supported locales.

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

        Raises: ConfigurationError if the configuration file doesn't exists
                or if something goes wrong while reading options from it.

        Params: cfg - path of the configuration file.

        """
        # Define a set of default values
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
            self.linksdir = config.get('links', 'dir')
            self.linksdir = os.path.join(self.basedir, self.linksdir)
        except ConfigParser.Error as e:
            logger.warning("Couldn't read 'links' from 'dir' (%s)" % cfg)
            raise ConfigurationError("Error with conf. See log file.")

        try:
            self.supported_locales = config.get('links', 'locales')
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

        # Keep log levels separated
        self.logger = utils.filter_logging(logger, self.logdir, self.loglevel)
        # self.logger.setLevel(logging.getLevelName(self.loglevel))
        self.logger.info('Redirecting logging to %s' % self.logdir)

        # Stop logging on stdout from now on
        self.logger.propagate = False
        self.logger.debug("New core object created")

    def get_links(self, service, operating_system, locale):
        """Get links for OS in locale.

        This method should be called from the services modules of
        GetTor (e.g. SMTP). To make it easy we let the module calling us
        specify the name of the service (for stats purpose).

        Raises: UnsupportedOSError: if the operating system is not supported.
                UnsupportedLocaleError: if the locale is not supported.
                InternalError: if something goes wrong while internally.

        Params: service - the name of the service trying to get the links.
                operating_system - the name of the operating system.
                locale - two-character string representing the locale.

        Returns: String with links.

        """

        # Which module called us and what was asking for?
        self.logger.info("%s did a request for %s, %s." %
                         (service, operating_system, locale))

        if locale not in self.supported_locales:
            self.logger.warning("Request for unsupported locale: %s" % locale)
            raise UnsupportedLocaleError("Locale %s not supported at the "
                                         "moment" % locale)

        if operating_system not in self.supported_os:
            self.logger.warning("Request for unsupported operating system: %s"
                                % operating_system)
            raise UnsupportedOSError("Operating system %s not supported at the"
                                     "moment" % operating_system)

        # This could change in the future, let's leave it isolated.
        links = self._get_links(operating_system, locale)

        if links is None:
            self.logger.error("Couldn't get the links", exc_info=True)
            raise InternalError("Something went wrong internally. See logs for"
                                " detailed info.")

        self.logger.info("Returning the links")
        return links

    def _get_links(self, operating_system, locale):
        """Internal method to get the links.

        Looks for the links inside each provider file. This should only be
        called from get_links() method.

        Returns: String with the links on success.
                 None on failure.

        Params: operating_system - name of the operating system
                locale: two-character string representing the locale.

        """

        # Read the links files using ConfigParser
        # See the README for more details on the format used
        links = []

        # Look for files ending with .links
        p = re.compile('.*\.links$')

        for name in os.listdir(self.linksdir):
            path = os.path.abspath(os.path.join(self.linksdir, name))
            if os.path.isfile(path) and p.match(path):
                links.append(path)

        # Let's create a dictionary linking each provider with the links
        # found for operating_system and locale. This way makes it easy
        # to check if no links were found
        providers = {}

        self.logger.info("Reading links from providers directory")
        for name in links:
            self.logger.debug("Reading %s" % name)
            # We're reading files listed on linksdir, so they must exist!
            config = ConfigParser.ConfigParser()
            config.read(name)

            try:
                pname = config.get('provider', 'name')
            except ConfigParser.Error as e:
                self.logger.warning("Couldn't get 'name' from 'provider' (%s)"
                                    % name)
                raise InternalError("Error while reading %s links file. See "
                                    "log file" % name)

            self.logger.debug("Checking if %s has links for %s in %s" %
                              (pname, operating_system, locale))

            try:
                providers[pname] = config.get(operating_system, locale)
            except ConfigParser.Error as e:
                self.logger.warning("Couldn't get %s from %s (%s)" %
                                    (locale, operating_system, name))
                raise InternalError("Error while reading %s links file. See "
                                    "log file" % name)

            # Each provider must have a fingerprint of the key used to
            # sign the uploaded packages
            try:
                self.logger.debug("Trying to get fingerprint from %s", pname)
                fingerprint = config.get('key', 'fingerprint')
                providers[pname] = providers[pname] + "\nFingerprint: "
                providers[pname] = providers[pname] + fingerprint
                self.logger.debug("Fingerprint added %s", fingerprint)
            except ConfigParser.Error as e:
                self.logger.warning("Couldn't get 'fingerprint' from 'key' "
                                    "(%s)" % name)
                raise InternalError("Error while reading %s links file. See "
                                    "log file" % name)

        # Create the final links list with all providers
        all_links = []

        self.logger.debug("Joining all links found for %s in %s" %
                          (operating_system, locale))
        for key in providers.keys():
            all_links.append(
                "\n%s\n%s\n" % (key, ''.join(providers[key]))
            )

        if all_links:
            return "".join(all_links)
        else:
            self.logger.warning("Trying to get supported os and locales, but"
                                " no links were found")
            return None

    def get_supported_os(self):
        """Public method to get the list of supported operating systems.

        Returns: List of strings.

        """
        return self.supported_os.split(',')

    def get_supported_locales(self):
        """Public method to get the list of supported locales.

        Returns: List of strings.

        """
        return self.supported_locales.split(',')

    def create_links_file(self, provider, fingerprint):
        """Public method to create a links file for a provider.

        This should be used by all providers since it writes the links
        file with the proper format. It backs up the old links file
        (if exists) and creates a new one.

        Params: provider - provider's name (links file will use this
                name in lower case).

                fingerprint: fingerprint of the key that signed the packages
                to be uploaded to the provider.

        """
        linksfile = os.path.join(self.linksdir, provider.lower() + '.links')
        linksfile_backup = ""
        self.logger.info("Request to create new %s" % linksfile)

        if os.path.isfile(linksfile):
            # Backup the old file in case something fails
            linksfile_backup = linksfile + '.backup'
            self.logger.info("Backing up %s to %s"
                             % (linksfile, linksfile_backup))
            os.rename(linksfile, linksfile_backup)

        try:
            # This creates an empty links file (with no links)
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
                self.logger.info("New %s created" % linksfile)
        except Exception as e:
            if linksfile_backup:
                os.rename(linksfile_backup, linksfile)
            raise LinkFileError("Error while trying to create new links file.")

    def add_link(self, provider, operating_system, locale, link):
        """Public method to add a link to a provider's links file.

        Use ConfigParser to add a link into the operating_system
        section, under the locale option. It checks for valid format;
        the provider's script should use the right format (see design).

        Raises: UnsupportedOSError: if the operating system is not supported.
                UnsupportedLocaleError: if the locale is not supported.
                LinkFileError: if there is no links file for the provider.
                LinkFormatError: if the link format doesn't seem legit.
                InternalError: if the links file doesn't have a section for the
                               OS requested. This *shouldn't* happen because
                               it means the file wasn't created correctly.

        Params: provider - name of the provider.
                operating_system - name of the operating system.
                locale - two-character string representing the locale.
                link - string to be added. The format should be as follows:

                https://pkg_url https://asc_url

                where pkg_url is the url for the bundle and asc_url is the
                url for the asc of the bundle.

        """
        linksfile = os.path.join(self.linksdir, provider.lower() + '.links')

        # Don't try to add unsupported stuff
        if locale not in self.supported_locales:
            self.logger.warning("Trying to add link for unsupported locale: %s"
                                % locale)
            raise UnsupportedLocaleError("Locale %s not supported at the "
                                         "moment" % locale)

        if operating_system not in self.supported_os:
            self.logger.warning("Trying to add link for unsupported operating "
                                "system: %s" % operating_system)
            raise UnsupportedOSError("Operating system %s not supported at the"
                                     " moment" % operating_system)

        # Check if the link has a legit format
        # e.g. https://db.tt/JjfUTb04 https://db.tt/MEfUTb04
        p = re.compile('^https://.+\shttps://.+$')

        if not p.match(link):
            self.logger.warning("Trying to add an invalid link: %s"
                                % link)
            raise LinkFormatError("Link '%s' doesn't seem to have a valid "
                                  "format" % link)

        if os.path.isfile(linksfile):
            content = ConfigParser.RawConfigParser()
            content.readfp(open(linksfile))
            # Check if exists and entry for locale; if not, create it
            try:
                links = content.get(operating_system, locale)
                links = links + ",\n" + link
                content.set(operating_system, locale, links)
                with open(linksfile, 'w') as f:
                    content.write(f)
                self.logger.info("Link %s added to %s %s in %s"
                                 % (link, operating_system, locale, provider))
            except ConfigParser.NoOptionError:
                content.set(operating_system, locale, link)
                with open(linksfile, 'w') as f:
                    content.write(f)
                self.logger.info("Link %s added to %s-%s in %s"
                                 % (link, operating_system, locale, provider))
            except ConfigParser.NoSectionError:
                # This shouldn't happen, but just in case
                self.logger.error("Unknown section %s in links file")
                raise InternalError("Unknown %s section in links file"
                                    % operating_system)
        else:
            raise LinkFileError("There is no links file for %s" % provider)
