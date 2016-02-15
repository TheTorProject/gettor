# -*- coding: utf-8 -*-
#
# This file is part of GetTor.
#
# :authors: Israel Leiva <ilv@torproject.org>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2015, The Tor Project, Inc.
#               (c) 2015, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

import os
import re
import json
import codecs
import urllib2
import ConfigParser

from time import gmtime, strftime


"""Script to build a static mirror of GetTor RESTful API"""

# currently supported locales for Tor Browser
LC = ['ar', 'de', 'en-US', 'es-ES', 'fa', 'fr', 'it', 'ko', 'nl', 'pl',
      'pt-PT', 'ru', 'tr', 'vi', 'zh-CN']

# https://gitweb.tpo/tor-browser-spec.git/tree/processes/VersionNumbers
# does not say anything about operating systems, so it's possible the
# notation might change in the future. We should always use the same three
# strings though: linux, windows, osx.
OS = {
    'Linux': 'linux',
    'Windows': 'windows',
    'MacOS': 'osx'
}

# based on
# https://gitweb.tpo.org/tor-browser-spec.git/tree/processes/VersionNumbers
# except for the first one, which is based on current RecommendedTBBVersions
RE = {
    'os': '(.*)-(\w+)',
    'alpha': '\d\.\d(\.\d)*a\d+',
    'beta': '\d\.\d(\.\d)*b\d+',
    'stable': '\d\.\d(\.\d)*'
}

# strings to build names of packages depending on OS.
PKG = {
    'windows': 'torbrowser-install-%s_%s.exe',
    'linux': 'tor-browser-linux%s-%s_%s.tar.xz',
    'osx': 'TorBrowser-%s-osx64_%s.dmg'
}

# bin and asc are used to build the download links for each version, os and lc
URL = {
    'version': 'https://gettor.torproject.org/api/latest.json',
    'mirrors': 'https://gettor.torproject.org/api/mirrors.json',
    'providers': 'https://gettor.torproject.org/api/providers.json'
}

GETTOR_URL = 'http://gettor.torproject.org'
SERVER_URL = 'https://yourprivateserver.com'
API_TREE = '/home/ilv/Proyectos/tor/static_api/'

class ConfigError(Exception):
    pass


class InternalError(Exception):
    pass


class APIMirror(object):
    """ Provide useful resources via RESTful API. """
    def __init__(self, cfg=None):
        self.url = SERVER_URL
        self.tree = API_TREE

    def _is_json(self, my_json):
        """ Check if json generated is valid.

        :param: my_json (string) data to ve verified.

        :return: (bool) true if data is json-valid, false otherwise.

        """
        try:
            json_object = json.loads(my_json)
        except ValueError, e:
            return False
        return True
    
    def _write_json(self, path, content):
        """
        """
        try:
            with codecs.open(
                path,
                "w",
                "utf-8"
            ) as jsonfile:
                # Make pretty json
                json.dump(
                    content,
                    jsonfile,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                    encoding="utf-8",
                )
        except IOError as e:
            #logging.error("Couldn't write json: %s" % str(e))
            print "Error building %s: %s" % (path, str(e))
        print "%s built" % path

    def _get_provider_name(self, p):
        """ Return simplified version of provider's name.

        :param: p (string) provider's name.

        :return: (string) provider's name in lowercase and without spaces.

        """
        p = p.replace(' ', '-')
        return p.lower()


    def _load_latest_version(self):
        """ Load latest version data from GetTor API. """
        response = urllib2.urlopen(URL['version'])
        json_response = json.load(response)
        self.lv = json_response

    def _load_links(self):
        """ Load links and providers data. """

        response = urllib2.urlopen(URL['providers'])
        json_response = json.load(response)
        
        links = {}
        
        for provider in json_response:
            if provider != 'updated_at':
                provider_url = json_response[provider]
            
                provider_response = urllib2.urlopen("%s.json" % provider_url)
                provider_content = json.load(provider_response)
                
                json_response[provider] = provider_url.replace(
                    GETTOR_URL,
                    self.url
                )

                
                links[provider] = provider_content

        self.providers = json_response
        self.links = links

    def _load_mirrors(self):
        """ Load mirrors data from GetTor API. """
        response = urllib2.urlopen(URL['mirrors'])
        json_response = json.load(response)
        self.mirrors = json_response

    def _load_resources(self):
        """ Load available resources data. """

        self.resources = {
            'providers': '%s/providers' % self.url,
            'mirrors': '%s/mirrors' % self.url,
            'latest_version': '%s/latest' % self.url,
            'updated_at': strftime("%Y-%m-%d %H:%M:%S", gmtime())
        }

    def load_data(self):
        """ Load all data."""
        self._load_links()
        self._load_mirrors()
        self._load_resources()
        self._load_latest_version()

    def build(self):
        """ Build RESTful API. """
        
        print "Building API mirror"
        
        # resources
        self._write_json(
            os.path.join(self.tree, 'api'),
            self.resources
        )

        api_path = os.path.join(self.tree, 'api-content')
        if not os.path.isdir(api_path):
            os.mkdir(api_path)
        
        # providers
        self._write_json(
            os.path.join(api_path, 'providers'),
            self.providers
        )

        providers_path = os.path.join(api_path, 'providers-content')
        if not os.path.isdir(providers_path):
            os.mkdir(providers_path)

        for provider in self.links:
            if provider == 'updated_at':
                continue

            self._write_json(
                os.path.join(providers_path, provider),
                self.links[provider]
            )

            provider_path = os.path.join(
                providers_path,
                "%s-content" % provider
            )

            if not os.path.isdir(provider_path):
                os.mkdir(provider_path)
            
            for osys in self.links[provider]:
                self._write_json(
                    os.path.join(provider_path, osys),
                    self.links[provider][osys]
                )

                provider_os_path = os.path.join(
                    provider_path, "%s-content" % osys
                )            

                if not os.path.isdir(provider_os_path):
                    os.mkdir(provider_os_path)
                
                for lc in self.links[provider][osys]:
                    self._write_json(
                        os.path.join(provider_os_path, lc),
                        self.links[provider][osys][lc]
                    )

        # latest version
        self._write_json(
            os.path.join(api_path, 'latest'),
            self.lv
        )
        
        lv_path = os.path.join(api_path, 'latest-content')
        if not os.path.isdir(lv_path):
            os.mkdir(lv_path)

        for release in self.lv:
            if release == 'updated_at':
                continue

            self._write_json(
                os.path.join(lv_path, release),
                self.lv[release]
            )
            
            release_path = os.path.join(
                lv_path,
                "%s-content" % release
            )

            if not os.path.isdir(release_path):
                os.mkdir(release_path)
            
            for osys in self.lv[release]['downloads']:
                self._write_json(
                    os.path.join(release_path, osys),
                    self.lv[release]['downloads'][osys]
                )

                release_os_path = os.path.join(
                    release_path,
                    "%s-content" % osys
                )

                if not os.path.isdir(release_os_path):
                    os.mkdir(release_os_path)
                
                for lc in self.lv[release]['downloads'][osys]:
                    self._write_json(
                        os.path.join(release_os_path, lc),
                        self.lv[release]['downloads'][osys][lc]
                    )

        # mirrors
        self._write_json(
            os.path.join(api_path, 'mirrors'),
            self.mirrors
        )

def main():
    api = APIMirror()
    api.load_data()
    api.build()

if __name__ == '__main__':
    main()
