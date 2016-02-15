#!/usr/bin/env python

# This file is part of GetTor, a Tor Browser distribution system.

# :authors: Sukhbir Singh <sukhbir@torproject.org>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2015, The Tor Project, Inc.

# To read the log files and populate the db, run the script with `--logs' once
# every day and then clear the log files. To generate the report, run it with
# `--report', once (or twice?) a month.

# TODO: Logging? argparse?

import os
import sys
import ConfigParser
from datetime import datetime as dt

import sqlite3

CORE_CFG = "core.cfg"

CHANNELS = ["smtp", "xmpp", "twitter"]
LOG_FILES = [channel + ".log" for channel in CHANNELS]

DB = "gettor2.db"

OUTPUT = "report.log"

REPORT = """@ GetTor Report for {}

We received a total of {} requests in {}, with a peak of {} requests on {}.

[*] Request
{}

[*] OS
{}

[*] Language
{}

[*] Channel
{}

"""


class Report(object):
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read(CORE_CFG)

        self.log_dir = self.config.get("log", "dir")
        # This is defined in the sample log file.
        self.log_format = ["date", "request", "os", "locale"]

        self.conn = sqlite3.connect(DB)

    def db_write(self):
        self.cursor = self.conn.cursor()
        for each in self.logs:
            self.cursor.execute("""INSERT INTO requests
                                (date, request, os, locale, channel) VALUES
                                (:date, :request, :os, :locale, :channel)""",
                                each)
            self.conn.commit()
        self.conn.close()

    def get_logs(self):
        self.logs = []
        for each in LOG_FILES:
            with open(os.path.join(self.log_dir, each)) as f:
                for line in f:
                    if line.startswith("[INFO] "):
                        # The "7" here is for the "[INFO] " text.
                        logs = [log.strip() for log in line[7:].split(";")]
                        log_data = {key: value for key, value in
                                    zip(self.log_format, logs)}
                        # We also need the channel.
                        log_data["channel"] = each.split(".")[0]
                        self.logs.append(log_data)
        self.db_write()
        self.conn.close()

    def generate_report(self):
        self.cursor = self.conn.cursor()
        self.requests = []

        self.cursor.execute("SELECT COUNT(*) FROM requests")
        self.requests.append(self.cursor.fetchone())

        self.cursor.execute("""SELECT date, COUNT(*) FROM requests
GROUP BY date
ORDER BY COUNT(date)
DESC""")
        self.requests.append(self.cursor.fetchone())

        self.columns = ["request", "os", "locale", "channel"]
        for each in self.columns:
            self.cursor.execute("""SELECT {0}, COUNT(*) FROM requests
GROUP BY {0}
ORDER BY COUNT({0})
DESC""".format(each))
            result = "\n".join(["{0:>16}: {1}".format(each[0], each[1])
                                for each in self.cursor.fetchall()
                                if not each[0] == "none"])
            self.requests.append(result)

        with open(OUTPUT, "a") as f:
            f.write(REPORT.format(dt.now().strftime("%B %Y"),
                                  self.requests[0][0],
                                  dt.now().strftime("%B"),
                                  self.requests[1][1],
                                  dt.strptime(self.requests[1][0], "%Y-%m-%d")
                                  .strftime("%B %-d"),
                                  *self.requests[2:]))
        self.conn.close()

if __name__ == "__main__":
    try:
        if sys.argv[1] == "--logs":
            Report().get_logs()
        if sys.argv[1] == "--report":
            Report().generate_report()
    except IndexError:
        sys.exit("You need either `--logs' or `--report.'")
