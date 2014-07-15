import os
import re
import inspect
import logging
import tempfile
import ConfigParser

"""
    GetTor main module.

    Classes:
        SingleLevelFilter: Filter logging levels.
        Core: Get links from providers.

    Methods:
        SingleLevelFilter.filter(): Filter logging levels. All except
                                    the one specified will be filtered.

        Core.get_links(): Get the links. It throws ValueError and
                          RuntimeError on failure.

        Core.create_links_file(): Create a file to store links of a given
                                  provider.

        Core.add_link(): Add a link to a links file of a given provider.

    Exceptions:
        ValueError: Request for an unsupported locale/operating system.
        RuntimeError: Something went wrong internally.
"""


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


class Core(object):
    """
        Gets links from providers and delivers them to other modules.

        Public methods:
            get_links(operating_system, locale)
    """

    def __init__(self, config_file):
    	"""
            Initialize a new object by reading a configuration file.

            Raises a RuntimeError if the configuration file doesn't exists
            or if something goes wrong while reading options from it.

            Arguments:
                config_file: path for the configuration file
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
            self.linksdir = self._get_config_option('links', 'dir', config)
            self.linksdir = os.path.join(self.basedir, self.linksdir)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.supported_locales = self._get_config_option('links',
                                                             'locales',
                                                             config)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.supported_os = self._get_config_option('links', 'os', config)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.loglevel = self._get_config_option('log', 'level', config)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

        try:
            self.logdir = self._get_config_option('log', 'dir', config)
            self.logdir = os.path.join(self.basedir, self.logdir)
        except RuntimeError as e:
            logger.warning("%s misconfigured. %s" % (config_file, str(e)))

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
        logger.info('Redirecting logging to %s' % self.logdir)

        # Stop logging on stdout from now on
        logger.propagate = False
        self.logger.debug("New core object created")

    def get_links(self, service, operating_system, locale):
        """
            Public method to obtain links.

            Checks for supported locales and operating systems. It returns
            ValueError if the locale or operating system is not supported.
            It raises RuntimeError if something goes wrong while trying
            to obtain the links. It returns a string on success. This
            method should be called from the services modules of GetTor
            (e.g. SMTP).
        """

        # Which module called us and what was asking for?
        self.logger.info("%s did a request for %s, %s." %
                         (service, operating_system, locale))

        if locale not in self.supported_locales:
            self.logger.warning("Request for unsupported locale: %s" % locale)
            raise ValueError("Locale %s not supported at the moment" % locale)

        if operating_system not in self.supported_os:
            self.logger.warning("Request for unsupported operating system: %s"
                                % operating_system)
            raise ValueError("Operating system %s not supported at the moment"
                             % operating_system)

        # This could change in the future, let's leave it isolated.
        links = self._get_links(operating_system, locale)

        if links is None:
            self.logger.error("Couldn't get the links", exc_info=True)
            raise RuntimeError("Something went wrong internally. See logs for \
                                detailed info.")

        self.logger.info("Returning the links")
        return links

    def _get_links(self, operating_system, locale):
        """
            Private method to obtain the links.

            Looks for the links inside each provider file. On success
            returns a string with the links. On failure returns None.
            This should only be called from get_links() method.

            Parameters:
                os: string describing the operating system
                locale: string describing the locale
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
        # to check if no links were found.
        providers = {}

        self.logger.info("Reading links from providers directory")
        for name in links:
            self.logger.debug("-- Reading %s" % name)
            # We're reading files listed on linksdir, so they must exist!
            config = ConfigParser.ConfigParser()
            config.read(name)

            try:
                pname = self._get_config_option('provider',
                                                'name', config)
            except RuntimeError as e:
                self.logger.warning("Links misconfiguration %s" % str(e))

            self.logger.debug("-- Checking if %s has links for %s in %s" %
                              (pname, operating_system, locale))

            try:
                providers[pname] = self._get_config_option(operating_system,
                                                           locale, config)
            except RuntimeError as e:
                self.logger.warning("-- Links misconfiguration %s" % str(e))
                
            # Each provider must have a fingerprint of the key used to 
            # sign the uploaded packages
            try:
                self.logger.debug("-- Trying to get fingerprint from %s",
                                  pname)
                fingerprint = self._get_config_option('key', 'fingerprint',
                                                      config)
                providers[pname] = providers[pname] + "\nFingerprint: "
                providers[pname] = providers[pname] + fingerprint
                self.logger.debug("-- Fingerprint added %s", fingerprint)
            except ValueError as e:
                self.logger.warning("-- No fingerprint found for provider %s" %
                                    pname)

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
            self.logger.warning("Trying to get supported os and locales, but \
                                 no links were found")
            return None

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

    def create_links_file(self, provider, fingerprint):
        """
            Public method to create a links file for a provider.

            This should be used by all providers since it writes the links
            file with the proper format. It backs up the old links file
            (if exists) and creates a new one. The name for the links file
            is the provider's name in lowercase. It receives the fingerprint
            of the key that signed the packages. 
            
            It raises a general exception if something goes wrong while 
            creating the new file.

            Arguments:
                provider: Provider's name. The links file will use this
                          name in lower case.
                fingerprint: Fingerprint of the key that signed the packages
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

    def add_link(self, provider, operating_system, locale, link):
        """
            Public method to add a link to a provider's links file.

            It uses ConfigParser to add a link into the operating_system
            section, under the locale option. It check for valid format;
            the provider's script should use the right format (see design).
            It raises ValueError in case the operating_system or locale
            are not supported (see config file for supported ones), or if
            if there is not a section for the operating_system in the
            links file, or if there is no links file for the given provider.
        """
        linksfile = os.path.join(self.linksdir, provider.lower() + '.links')

        # Don't try to add unsupported stuff
        if locale not in self.supported_locales:
            self.logger.warning("Trying to add link for unsupported locale: %s"
                                % locale)
            raise ValueError("Locale %s not supported at the moment" % locale)

        if operating_system not in self.supported_os:
            self.logger.warning("Trying to add link for unsupported operating \
                                system: %s" % operating_system)
            raise ValueError("Operating system %s not supported at the moment"
                             % operating_system)

        # Check if seems legit format
        # e.g. https://foo.bar https://foo.bar.asc 111-222-333-444
        # p = re.compile('^https://\.+\shttps://\.+\s\.+$')

        # if p.match(link):
        #    self.logger.warning("Trying to add an invalid link: %s"
        #                         % link)
        #    raise ValueError("The link %s doesn't seem to have a valid format"
        #                      % link)

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
                raise ValueError("Unknown %s section in links file"
                                 % operating_system)
        else:
            raise ValueError("There is no links file for %s" % provider)
