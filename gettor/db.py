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

import time
import sqlite3
import datetime

"""DB interface for comunicating with sqlite3"""


class DB(object):
    """

    Public methods:

        add_request(): add a request to the database (requests table).
        get_user(): get user info from the database (users table).
        add_user(): add a user to the database (users table).
        update_user(): update a user on the database (users table).

    """

    def __init__(self, dbname):
    	"""Create a new db object.

        :param: dbname (string) the path of the database.

        """
        self.con = sqlite3.connect(dbname)
        self.con.row_factory = sqlite3.Row

    def add_request(self):
        """Add a request to the database.

        For now we just count the number of requests we have received so far.

        """
        with self.con:
            cur = self.con.cursor()
            cur.execute("SELECT counter FROM requests WHERE id = 1")
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE requests SET counter=? WHERE id=?",
                            (row['counter']+1, 1))
            else:
                cur.execute("INSERT INTO requests VALUES(?, ?)", (1, 1))

    def get_user(self, user, service):
        """Get user info from the database.

        :param: user (string) unique (hashed) string that represents the user.
        :param: service (string) the service related to the user (e.g. SMTP).

        :return: (dict) the user information, with fields as indexes
                 (e.g. row['user']).

        """
        with self.con:
            cur = self.con.cursor()
            cur.execute("SELECT * FROM users WHERE id =? AND service =?",
                        (user, service))

            row = cur.fetchone()
            return row

    def add_user(self, user, service, blocked):
        """Add a user to the database.

        We add a user with one 'times' and the current time as 'last_request'
        by default.

        :param: user (string) unique (hashed) string that represents the user.
        :param: service (string) the service related to the user (e.g. SMTP).
        :param: blocked (int) one if user is blocked, zero otherwise.

        """
        with self.con:
            cur = self.con.cursor()
            cur.execute("INSERT INTO users VALUES(?,?,?,?,?)",
                        (user, service, 1, blocked, str(time.time())))

    def update_user(self, user, service, times, blocked):
        """Update a user on the database.

        We update the user info with the current time as 'last_request'.

        :param: user (string) unique (hashed) string that represents the user.
        :param: service (string) the service related to the user (e.g. SMTP).
        :param: times (int) the number of requests the user has made.
        :param: blocked (int) one if user is blocked, zero otherwise.

        """
        with self.con:
            cur = self.con.cursor()
            cur.execute("UPDATE users SET times =?, blocked =?,"
                        " last_request =? WHERE id =? AND service =?",
                        (times, blocked, str(time.time()), user, service))
