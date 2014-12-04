#!/usr/bin/env python

# Copyright (C) 2014 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

#TODO make this use the rinex ephemeris format, instead of my custom junk

import datetime
import pandas as pd
import numpy as np

def _parse_epoch(t):
    year = int(t[1:3])
    if year >= 80:
        year += 1900
    else:
        year += 2000
    month = int(t[4:6])
    day = int(t[7:9])
    hour = int(t[10:12])
    minute = int(t[13:15])
    second = int(t[15:18])
    microsecond = int(t[19:25]) # Discard the least sig. fig. (use microseconds only).
    return datetime.datetime(year, month, day, hour, minute, second, microsecond)

def ephemeris_file(filename):
    # TODO parse RINEX instead
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    header = lines[0][:164].replace(' ','').split(',')[1:]
    fields = np.array(map(lambda x: x.split(','),lines[1:]))
    times = fields[:,0]
    fields = np.array(fields[:,1:], dtype='double')
    return pd.DataFrame(fields,index=map(_parse_epoch,times), columns=header)

def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="the ephemeris file to process")
    parser.add_argument("output",
                        help="the output HDF5 file name")
    args = parser.parse_args()

    rf = ephemeris_file(args.input)

    rf.to_hdf(args.output,'eph')

if __name__ == '__main__':
    main()

