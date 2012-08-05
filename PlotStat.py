# Copyright 2012 The Tor Project

import os
import sys
import pylab
import matplotlib
import matplotlib.dates
from optparse import OptionParser
from datetime import datetime

def parse_args():
  parser = OptionParser()
  parser.add_option("-g", "--gettor-stats-file", default = "gettor_stats.txt", help = "Path to GetTor statistics file (default: %default)", metavar = "FILE")
  parser.add_option("-s", "--start-date", help = "Start graph on given date (format: YYYY-MM-DD)", metavar = "DATE")
  parser.add_option("-e", "--end-date", help = "End graph on given date (format: YYYY-MM-DD)", metavar = "DATE")
  parser.add_option("-l", "--language", help = "Plot only packages for a given language code ('en', 'fa', 'zh_CN', etc.)", metavar = "LANG")
  parser.add_option("-d", "--dpi", type = "int", default = 72, help = "Resolution in dpi (default: %default)", metavar = "NUM")
  (options, args) = parser.parse_args()
  if not os.path.exists(options.gettor_stats_file):
    parser.error("Did not find gettor_stats.txt.  Download from http://gettor.torproject.org:8080/~gettor/gettor_stats.txt.")
  return options

def read_gettor_stats_file(gettor_stats_file, start_date = None, end_date = None, language = None):
  data = {}
  with open(gettor_stats_file) as file:
    for line in file.readlines():
      line = line.strip()
      if not line:
        continue
      parts = line.split()
      date = parts[0]
      if start_date and date < start_date:
        continue
      if end_date and date > end_date:
        continue
      for part in parts[2:]:
        key, value = part.split(":")
        if key == "None" or value == "0":
          continue
        if language and not key.endswith("_" + language):
          continue
        if data.has_key(date):
          data[date] += int(value)
        else:
          data[date] = int(value)
  del data[max(data.keys())]
  return data

def plot_gettor_stats(gettor_data, language = None, dpi = 72):
  dates = sorted(gettor_data.keys())
  datetimes = [datetime.strptime(date, "%Y-%m-%d") for date in dates]
  values = [int(gettor_data[date]) for date in dates]
  fig = pylab.figure()
  ax = fig.gca()
  ax.plot_date(pylab.date2num(datetimes), values, linestyle='-')
  ax.grid(True)
  ax.set_ybound(lower = 0)
  if len(dates) < 30:
    ax.xaxis.set_major_locator(matplotlib.dates.WeekdayLocator(byweekday = matplotlib.dates.MO))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b %d, %Y'))
  if language:
    title = "Packages (language: %s) requested from GetTor per day" % language
  else:
    title = "Total packages requested from GetTor per day"
  pylab.title(title)
  pylab.savefig("gettor.png", format = "png", dpi = dpi)

if __name__ == "__main__":
  options = parse_args()
  data = read_gettor_stats_file(gettor_stats_file = options.gettor_stats_file,
                                start_date = options.start_date, end_date = options.end_date,
                                language = options.language)
  plot_gettor_stats(data, language = options.language, dpi = options.dpi)

