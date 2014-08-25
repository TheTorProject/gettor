#!/usr/bin/python
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


import sqlite3
import argparse


def main():
    """Script for showing stats.

    See argparse usage for more details.

    """
    parser = argparse.ArgumentParser(description='Utility for GetTor stats')
    parser.add_argument('database', metavar='database.db', type=str,
                        help='the database file')
    parser.add_argument('-s', '--service', default=None,
                        help='filter by service')
    parser.add_argument('-t', '--type', default=None,
                        help='filter by type of request')
    parser.add_argument('-o', '--os', default=None,
                        help='filter by OS')
    parser.add_argument('-l', '--lc', default=None,
                        help='filter by locale')
    parser.add_argument('-p', '--pt', default=None,
                        help='filter by PT requests')
    parser.add_argument('-y', '--year', default=None,
                        help='filter by year')
    parser.add_argument('-m', '--month', default=None,
                        help='filter by month')
    parser.add_argument('-d', '--day', default=None,
                        help='filter by day')
    parser.add_argument('-u', '--status', default=None,
                        help='filter by status of the request')

    args = parser.parse_args()
    query = 'SELECT * FROM requests'
    has_where = False

    # we build the query piece by piece
    if args.service:
        query = "%s %s" % (query, "WHERE service = '%s'" % args.service)
        has_where = True
    if args.type:
        if has_where:
            query = "%s %s" % (query, "AND type = '%s'" % args.type)
        else:
            query = "%s %s" % (query, "WHERE type = '%s'" % args.type)
            has_where = True
    if args.os:
        if has_where:
            query = "%s %s" % (query, "AND os = '%s'" % args.os)
        else:
            query = "%s %s" % (query, "WHERE os = '%s'" % args.os)
            has_where = True
    if args.lc:
        if has_where:
            query = "%s %s" % (query, "AND lc = '%s'" % args.lc)
        else:
            query = "%s %s" % (query, "WHERE lc = '%s'" % args.lc)
            has_where = True
    if args.pt:
        if has_where:
            query = "%s %s" % (query, "AND pt = %s" % args.pt)
        else:
            query = "%s %s" % (query, "WHERE pt = %s" % args.pt)
            has_where = True
    if args.year:
        if has_where:
            query = "%s %s" % (query, "AND year = %s" % args.year)
        else:
            query = "%s %s" % (query, "WHERE year = %s" % args.year)
            has_where = True
    if args.month:
        if has_where:
            query = "%s %s" % (query, "AND month = %s" % args.month)
        else:
            query = "%s %s" % (query, "WHERE month = %s" % args.month)
            has_where = True
    if args.day:
        if has_where:
            query = "%s %s" % (query, "AND day = %s" % args.day)
        else:
            query = "%s %s" % (query, "WHERE day = %s" % args.day)
            has_where = True
    if args.status:
        if has_where:
            query = "%s %s" % (query, "AND status = '%s'" % args.status)
        else:
            query = "%s %s" % (query, "WHERE status = '%s'" % args.status)
            has_where = True

    con = sqlite3.connect(args.database)

    with con:
        cur = con.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        # show it nice
        print "\nNumber of results: %s\n" % len(rows)
        cns = [cn[0] for cn in cur.description]
        print "%-10s %-10s %-10s %-10s %-10s %-10s %-10s %-10s"\
              " %-15s %s"\ % (cns[0], cns[1], cns[2], cns[3], cns[4], cns[5],
                              cns[6], cns[7], cns[8], cns[9])

        for row in rows:
            print "%-10s %-10s %-10s %-10s %-10s %-10s %-10s %-10s"\
                  " %-15s %s" % (row[0], row[1], row[2], row[3], row[4],
                                 row[5], row[6], row[7], row[8], row[9])

if __name__ == "__main__":
    main()
