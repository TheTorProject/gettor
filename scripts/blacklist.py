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

import sys
import time
import sqlite3
import argparse


def main():
    """Script for managing blacklisting of users.

    See argparse usage for more details.

    """
    parser = argparse.ArgumentParser(description='Utility for GetTor'
                                     ' blacklisting')
    parser.add_argument('database', metavar='database.db', type=str,
                        help='the database file')
    parser.add_argument('-u', '--user', default=None,
                        help='filter by user hash')
    parser.add_argument('-s', '--service', default=None,
                        help='filter by service')
    parser.add_argument('-b', '--blocked', default=None,
                        help='filter by blocked users')
    parser.add_argument('-a', '--add', default=None, nargs=3,
                        metavar=('USER', 'SERVICE', 'BLOCKED'),
                        help='add user')
    parser.add_argument('-c', '--clean', default=None, const='c', nargs='?',
                        metavar='user hash',
                        help='clean table (delete expired blacklistings)')
    parser.add_argument('-r', '--requests', default=None,
                        help='number of requests; everyone with number of'
                        ' requests greather than this will be cleaned up')

    args = parser.parse_args()
    query = ''
    con = sqlite3.connect(args.database)

    if args.add:
        # add new entry, useful for adding users permanently blocked
        query = "INSERT INTO users VALUES('%s', '%s', 1, %s, %s)"\
                % (args.add[0], args.add[1], args.add[2], time.time())
        with con:
            cur = con.cursor()
            cur.execute(query)
        print "Query execute successfully"
    elif args.clean:
        if args.clean == 'c':
            if args.requests:
                # delete by number of times
                query = "DELETE FROM users WHERE times > %s" % args.requests
                with con:
                    cur = con.cursor()
                    cur.execute(query)
                print "Query executed successfully."
            else:
                sys.exit("Number of requests missing. See --help.")
        else:
            # delete by id
            query = "DELETE FROM users WHERE id='%s'" % args.clean
            with con:
                cur = con.cursor()
                cur.execute(query)
            print "Query execute succcessfully."
    else:
        query = "SELECT * FROM users"
        has_where = False
        # filter
        if args.service:
            query = "%s %s" % (query, "WHERE service='%s'" % args.service)
            has_where = True
        if args.user:
            if has_where:
                query = "%s %s" % (query, "AND id='%s'" % args.user)
            else:
                query = "%s %s" % (query, "WHERE id='%s'" % args.user)
                has_where = True
        if args.blocked:
            if has_where:
                query = "%s %s" % (query, "AND blocked=%s" % args.blocked)
                has_where = True
            else:
                query = "%s %s" % (query, "WHERE blocked=%s" % args.blocked)

        with con:
            cur = con.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            # show it nice
            print "\nNumber of results: %s\n" % len(rows)
            cns = [cn[0] for cn in cur.description]
            print "%-70s %-10s %-10s %-10s %-s" % (cns[0], cns[1], cns[2],
                                                   cns[3], cns[4])

            for row in rows:
                print "%-70s %-10s %-10s %-10s %s" % (row[0], row[1], row[2],
                                                      row[3], row[4])

if __name__ == "__main__":
    main()
