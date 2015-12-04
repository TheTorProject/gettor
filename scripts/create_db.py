#!/usr/bin/python
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
import sqlite3
import argparse


def main():
    """Create/delete GetTor database for managing stats and blacklisting.

    Database file (.db) must be empty. If it doesn't exist, it will be
    created. See argparse usage for more details.

    """
    parser = argparse.ArgumentParser(description='Utility for GetTor'
                                     ' database')
    parser.add_argument('-c', '--create', default=None,
                        metavar='path_to_database.db',
                        help='create database')
    parser.add_argument('-d', '--delete', default=None,
                        metavar='path_to_database.db',
                        help='delete database')

    args = parser.parse_args()
    if args.create:
        con = sqlite3.connect(args.create)
        with con:
            cur = con.cursor()
            # table for handling users (i.e. blacklist)
            cur.execute(
                "CREATE TABLE users(id TEXT, service TEXT, times INT,"
                "blocked INT, last_request TEXT)"
            )
            
            cur.execute(
                "CREATE TABLE requests(date TEXT, request TEXT, os TEXT,"
                " locale TEXT, channel TEXT, PRIMARY KEY (date, channel))"
            )

        print "Database %s created" % os.path.abspath(args.create)
    elif args.delete:
        os.remove(os.path.abspath(args.delete))
        print "Database %s deleted" % os.path.abspath(args.delete)
    else:
        print "See --help for details on usage."
if __name__ == "__main__":
    main()
