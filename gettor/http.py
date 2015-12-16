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

from flask import Flask
from flask_restful import Api, Resource, reqparse

import core
import utils

"""GetTor RESTful API"""

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
    'version': 'https://www.torproject.org/projects/torbrowser/RecommendedTBBVersions',
    'bin': 'https://www.torproject.org/dist/torbrowser/%s/%s',
    'asc': 'https://www.torproject.org/dist/torbrowser/%s/%s.asc'
}

# filters for API resources
parser = reqparse.RequestParser()
parser.add_argument('os', type=str, help='Operating System')
parser.add_argument('lc', type=str, help='Locale')


class ConfigError(Exception):
    pass


class InternalError(Exception):
    pass


class HTTP(object):
    """ Provide useful resources via RESTful API. """
    def __init__(self, cfg=None):
        """ Create new object by reading a configuration file.

        :param: cfg (string) path of the configuration file.

        """
        default_cfg = 'http.cfg'
        config = ConfigParser.ConfigParser()

        if cfg is None or not os.path.isfile(cfg):
            cfg = default_cfg

        try:
            with open(cfg) as f:
                config.readfp(f)
        except IOError:
            raise ConfigError("File %s not found!" % cfg)

        try:
            # server that provides the RESTful API
            self.server = config.get('general', 'server')
            # path to the links files
            self.links_path = config.get('general', 'links')
            # path to mirrors in json
            self.mirrors_path = config.get('general', 'mirrors')

            # we will ask gettor.core for the links
            core_cfg = config.get('general', 'core')
            self.core = core.Core(core_cfg)

        except ConfigParser.Error as e:
            raise ConfigError("Configuration error: %s" % str(e))
        except core.ConfigError as e:
            raise InternalError("HTTP error: %s" % str(e))

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

    def _get_provider_name(self, p):
        """ Return simplified version of provider's name.

        :param: p (string) provider's name.

        :return: (string) provider's name in lowercase and without spaces.

        """
        p = p.replace(' ', '-')
        return p.lower()

    def _add_links(self, lv, release, version, os):
        """ Add link for all locales in LC depending on given OS.

        :param: lv (dict) latest version data structure.
        :param: release (string) release to which add the links.
        :param: version (string) version obtained from tpo.
        :param: os (string) operating system.

        """
        for lc in LC:
            if os == 'linux':
                pkg32 = PKG['linux'] % ('32', version, lc)
                link_bin32 = URL['bin'] % (version, pkg32)
                link_asc32 = URL['asc'] % (version, pkg32)

                pkg64 = PKG['linux'] % ('64', version, lc)
                link_bin64 = URL['bin'] % (version, pkg64)
                link_asc64 = URL['asc'] % (version, pkg64)

                lv[release]['downloads'][os][lc] = {
                    'binary32': link_bin32,
                    'signature32': link_asc32,
                    'binary64': link_bin64,
                    'signature64': link_asc64,
                }
            else:
                if os == 'windows':
                    pkg = PKG['windows'] % (version, lc)

                elif os == 'osx':
                    pkg = PKG['osx'] % (version, lc)

                else:
                    continue

                link_bin = URL['bin'] % (version, pkg)
                link_asc = URL['asc'] % (version, pkg)
                lv[release]['downloads'][os][lc] = {
                    'binary': link_bin,
                    'signature': link_asc
                }

    def _load_latest_version(self):
        """ Load latest version data. """
        response = urllib2.urlopen(URL['version'])
        json_response = json.load(response)

        lv = {
            'stable': {
                'latest_version': '',
                'downloads': {}
            },
            'alpha': {
                'latest_version': '',
                'downloads': {}
            },
            'beta': {
                'latest_version': '',
                'downloads': {}
            }
        }

        self.releases = {
            'alpha': '%s/latest/alpha' % self.server,
            'beta': '%s/latest/beta' % self.server,
            'stable': '%s/latest/stable' % self.server,
            'updated_at': strftime("%Y-%m-%d %H:%M:%S", gmtime())
        }

        # one iteration to find the latest version for each release
        for v in json_response:
            # latest version for each release
            if not re.match(RE['os'], v):
                if re.match(RE['alpha'], v):
                    if v > lv['alpha']['latest_version']:
                        # we'll use the latest one
                        lv['alpha']['latest_version'] = v

                elif re.match(RE['beta'], v):
                    if v > lv['beta']['latest_version']:
                        # we'll use the latest one
                        lv['beta']['latest_version'] = v

                elif re.match(RE['stable'], v):
                    if v > lv['stable']['latest_version']:
                        # we'll use the latest one
                        lv['stable']['latest_version'] = v

        latest_alpha = lv['alpha']['latest_version']
        latest_beta = lv['beta']['latest_version']
        latest_stable = lv['stable']['latest_version']

        # another iteration to add the links
        for v in json_response:
            # based on current RecommendedTBBVersions scheme
            # for each release and for each os we build links for all locales
            if re.match(RE['os'], v):
                m = re.match(RE['os'], v)
                version = m.group(1)
                osys = m.group(2)

                if osys in OS:
                    if latest_alpha and version == latest_alpha \
                            and re.match(RE['alpha'], version):
                        lv['alpha']['downloads'][OS[osys]] = {}
                        self._add_links(lv, 'alpha', version, OS[osys])

                    elif latest_beta and version == latest_beta \
                            and re.match(RE['beta'], version):
                        lv['beta']['downloads'][OS[osys]] = {}
                        self._add_links(lv, 'beta', version, OS[osys])

                    elif latest_stable and version == latest_stable \
                            and re.match(RE['stable'], version):
                        lv['stable']['downloads'][OS[osys]] = {}
                        self._add_links(lv, 'stable', version, OS[osys])

        lv['updated_at'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        self.lv = lv

    def _load_links(self):
        """ Load links and providers data. """
        links_files = []

        # look for files ending with .links in links_path
        p = re.compile('.*\.links$')
        for name in os.listdir(self.links_path):
            path = os.path.abspath(os.path.join(self.links_path, name))
            if os.path.isfile(path) and p.match(path):
                links_files.append(path)

        links = {}
        providers = {}
        supported_os = self.core.get_supported_os()
        supported_lc = self.core.get_supported_lc()

        for name in links_files:
            config = ConfigParser.ConfigParser()
            try:
                with open(name) as f:
                    config.readfp(f)
            except IOError:
                raise InternalError("File %s not found!" % name)

            try:
                pname = config.get('provider', 'name')
                pname = self._get_provider_name(pname)

                # build providers dict
                providers[pname] = '%s/providers/%s' % (self.server, pname)
                providers['updated_at'] = strftime(
                    "%Y-%m-%d %H:%M:%S", gmtime()
                )

                self.providers = providers
                links[pname] = {}

                # build links data.
                for osys in supported_os:
                    links[pname][osys] = {}
                    for lc in supported_lc:
                        links[pname][osys][lc] = {}

                for osys in supported_os:
                    for lc in supported_lc:
                        l_str = config.get(osys, lc)

                        # linux has 32 and 64 bit packages
                        if osys == 'linux':
                            l32_str, l64_str = l_str.split(',')

                            link32, sig32, sha32 = [
                                l for l in l32_str.split("$") if l
                            ]

                            link64, sig64, sha64 = [
                                l for l in l64_str.split("$") if l
                            ]
                            link64 = link64.lstrip()

                            links[pname][osys][lc]['binary32'] = link32
                            links[pname][osys][lc]['signature32'] = sig32
                            links[pname][osys][lc]['sha256-32'] = sha32
                            links[pname][osys][lc]['binary64'] = link64
                            links[pname][osys][lc]['signature64'] = sig64
                            links[pname][osys][lc]['sha256-64'] = sha64

                        else:
                            link, sig, sha = [l for l in l_str.split("$") if l]
                            links[pname][osys][lc]['binary'] = link
                            links[pname][osys][lc]['signature'] = sig
                            links[pname][osys][lc]['sha256'] = sha

            except ConfigParser.Error as e:
                raise InternalError("%s" % str(e))

        links['updated_at'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        self.links = links

    def _load_mirrors(self):
        """ Load mirrors data. """
        mirrors = []

        # json of mirrors should be obtained from get_mirrors.py
        json_data = open(self.mirrors_path).read()
        mirrors = json.loads(json_data)

        self.mirrors = mirrors

    def _load_resources(self):
        """ Load available resources data. """

        self.resources = {
            'providers': '%s/providers' % self.server,
            'mirrors': '%s/mirrors' % self.server,
            'latest_version': '%s/latest' % self.server,
            'updated_at': strftime("%Y-%m-%d %H:%M:%S", gmtime())
        }

    def load_data(self):
        """ Load all data.

        Since data is not frequently updated, we load all data before
        running the RESTful API. Every time the links/mirrors/version
        data is updated we should restart the API.

        """
        self._load_links()
        self._load_mirrors()
        self._load_resources()
        self._load_latest_version()

    def run(self):
        """ Run RESTful API. """
        app = Flask(__name__)
        api = Api(app)

        api.add_resource(
            AvailableResources,
            '/',
            resource_class_kwargs={
                'resources': self.resources
            }
        )

        api.add_resource(
            Providers,
            '/providers',
            '/providers/<string:provider>',
            resource_class_kwargs={
                'links': self.links,
                'providers': self.providers
            }
        )

        api.add_resource(
            LatestVersion,
            '/latest',
            '/latest/<string:release>',
            resource_class_kwargs={
                'latest_version': self.lv,
                'releases': self.releases
            }
        )

        api.add_resource(
            Mirrors,
            '/mirrors',
            resource_class_kwargs={
                'mirrors': self.mirrors
            }
        )

        app.run(debug=True)


class AvailableResources(Resource):
    def __init__(self, resources):
        """ Set initial data. """
        self.resources = resources

    def get(self):
        """ Return available resources on the API. """
        return self.resources


class Providers(Resource):
    def __init__(self, providers, links):
        """ Set initial data. """
        self.providers = providers
        self.links = links

    def get(self, provider=None):
        """ Return providers and links data. """

        # we use arg to filter results by os and lc (in that order)
        arg = parser.parse_args()

        if provider:
            if arg['os']:
                if arg['lc']:
                    # links by provider, os, and lc (in that order)
                    return self.links[provider][arg['os']][arg['lc']]
                else:
                    # links by provider and os (in that order)
                    return self.links[provider][arg['os']]
            else:
                # links by provider
                return self.links[provider]
        else:
            # list of providers
            return self.providers


class LatestVersion(Resource):
    def __init__(self, latest_version, releases):
        """ Set initial data. """
        self.lv = latest_version
        self.releases = releases

    def get(self, release=None):
        """ Return latest version data. """

        # we use arg to filter results by os and lc (in that order)
        arg = parser.parse_args()

        if release:
            if arg['os']:
                if arg['lc']:
                    # tpo links by release, os and lc (in that order)
                    return self.lv[release]['downloads'][arg['os']][arg['lc']]
                else:
                    # tpo links by release and os (in that order)
                    return self.lv[release]['downloads'][arg['os']]
            else:
                # version and tpo links by release
                return self.lv[release]
        else:
            # list of releases
            return self.releases


class Mirrors(Resource):
    def __init__(self, mirrors):
        """ Set initial data. """
        self.mirrors = mirrors

    def get(self):
        """ Return mirrors data. """
        return self.mirrors
