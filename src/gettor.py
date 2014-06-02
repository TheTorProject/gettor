import os
import re
import inspect
import logging


class Core:
    
    """
        Gets links from providers and delivers them to other modules.
        
        Public methods: 
            get_links(operating_system, locale)
    """
    
    def __init__(self):
    	"""
            Initialize a Core object by reading a configuration file.
            
            Parameters: none
    	"""
        
        # Read configuration file

        
        # Dummy info. This should be read from a configuration file.
        self.basedir = './providers/'
        self.supported_locales = [ 'en', 'es' ]
        self.supported_os = [ 'windows', 'linux', 'osx' ]
    
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
        
        # Log requests
        self._log_request(operating_system, locale)
        
        if locale not in self.supported_locales:
            raise ValueError("Locale %s not supported at the moment" % locale)
            
        if operating_system not in self.supported_os:
            raise ValueError("Operating system %s not supported at the moment" 
                             % operating_system)
            
        # This could change in the future, let's leave it isolated.
        links = self._get_links(operating_system, locale)
        
        if links is None:
            raise RuntimeError("Something went wrong with GetTor's core")      
        
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
        
        # There should be a 'providers' directory inside self.basedir
        #
        # Each .links file begins with a string describing the provider.
        # After that, every line should have the following format:
        # 
        # operating_system locale link package_signature key_fingerprint
        #
        # e.g. 
        #
        # Dropbox
        # linux en https://foo.bar https://foo.bar.asc 111-222-333-444
        # osx es https://bar.baz https://bar.baz.asc 555-666-777-888
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
        
        # We trust links have been generated properly
        for name in links:
            link_file = open(name, 'r')
            provider_name = link_file.readline()
            
            for line in link_file:
                words = line.split(' ')
                if words[0] == operating_system and words[1] == locale:
                    providers.setdefault(provider_name, []).append(
                        "%s %s %s" % (words[2], words[3], words[4].replace('-', ' '))
                    )
                    
            link_file.close()
             
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
        
        # Dummy print for now. Should be done with logging
        print "\nCalled by %s\nOS: %s\nLocale: %s\n" % \
        (str(module), operating_system, locale)
        
    
