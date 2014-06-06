import os
import re
import inspect
import logging
import ConfigParser

"""
    GetTor main module.

    Classes:
        Core: Get links from providers.

    Methods:
        Core.get_links(): Get the links. It throws ValueError and 
                          RuntimeError on failure.

    Exceptions:
        ValueError: Request for an unsupported locale/operating system.
        RuntimeError: Something went wrong internally.
"""


class Core:

    """
        Gets links from providers and delivers them to other modules.

        Public methods:
            get_links(operating_system, locale)
    """

    def __init__(self, config_file):
    	"""
            Initialize a Core object by reading a configuration file.

            Raises a RuntimeError if the configuration file doesn't exists.

            Parameters: none
        """

        logging.basicConfig()
        logger = logging.getLogger(__name__)

        config = ConfigParser.ConfigParser()

        if os.path.isfile(config_file):
            logger.debug("Reading configuration from %s" % config_file)
            config.read(config_file)
        else:
            logger.error("Error while trying to read %s" % config_file)
            raise RuntimeError("Couldn't read the configuration file %s"
                               % config_file)

        # To do: check for unspecified sections and/or options
        self.basedir = config.get('general', 'basedir')
        self.linksdir = config.get('links', 'linksdir')
        self.supported_locales = config.get('links', 'locales').split(', ')
        self.supported_os = config.get('links', 'os').split(', ')
        self.loglevel = config.get('log', 'loglevel')
        self.logdir = config.get('log', 'logdir')
        self.logger = logger
        self.logger.setLevel(logging.getLevelName(self.loglevel))

        self.logger.debug("New core object created")

    def get_links(self, operating_system, locale):
        """
            Public method to obtain links.

            Checks for supported locales and operating systems. It returns
            ValueError if the locale or operating system is not supported.
            It raises RuntimeError if something goes wrong while trying
            to obtain the links. It returns a string on success. This
            method should be called from the services modules of GetTor
            (e.g. SMTP).
        """

        self._log_request(operating_system, locale)

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
            raise RuntimeError("Something went wrong with GetTor's core")

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

        # We read the links files from the 'linksdir' inside 'basedir'
        #
        # Each .links file uses the ConfigParser's format.
        # There should be a section [provider] with the option 'name' for
        # the provider's name (e.g. Dropbox)
        #
        # Following sections should specify the operating system and its
        # options should be the locale. When more than one link is available
        # per operating system and locale (always) the links should be
        # specified as a multiline value. Each link has the format:
        #
        # link link_signature key_fingerprint
        #
        # e.g.
        #
        # [provider]
        # name: Dropbox
        #
        # [linux]
        # en: https://foo.bar https://foo.bar.asc 111-222-333-444,
        #     https://foo.bar https://foo.bar.asc 555-666-777-888
        #
        # es: https://bar.baz https://bar.baz.asc 555-666-777-888
        #
        links = []

        # Look for files ending with .links
        p = re.compile('.*\.links$')

        for name in os.listdir(self.basedir):
            path = os.path.abspath(os.path.join(self.basedir, name))
            if os.path.isfile(path) and p.match(path):
                links.append(path)

        # Let's create a dictionary linking each provider with the links
        # found for operating_system and locale. This way makes it easy
        # to check if no links were found.
        providers = {}

        self.logger.info("Reading links from providers directory")
        # We trust links have been generated properly
        config = ConfigParser.ConfigParser()
        for name in links:
            config.read(name)
            provider_name = config.get('provider', 'name')
            providers[provider_name] = config.get(operating_system, locale)

        # Create the final links list with all providers
        all_links = []

        for key in providers.keys():
            all_links.append(
                "\n%s\n%s\n" % (key, ''.join(providers[key]))
            )

        if all_links:
            return "".join(all_links)
        else:
            return None

    def _log_request(self, operating_system, locale):
        """
            Private method to log what service module called to get the links.

            Parameters: none
        """

        caller = inspect.stack()[2]
        module = inspect.getmodule(caller[0])

        self.logger.info("\n%s did a request for %s, %s\n" %
                         (str(module), operating_system, locale))
