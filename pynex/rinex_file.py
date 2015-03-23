#!/usr/bin/env python

# Copyright (C) 2014 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import datetime
import pandas
import numpy as np
from os.path import expanduser, splitext

def floatornan(x): #this is up to 1000x faster than original code
    return np.float64(x) if x.strip(None) else np.nan
#    if x == '' or x[-1] == ' ':
#        return np.NaN
#    else:
#        return np.float64(x)

def digitorzero(x): #this is up to 3000x faster than original code
    return int(x) if x.strip(None) else 0

def padline(l, n=16):
    x = len(l)
    x_ = n * ((x + n - 1) // n)
    return l + ' ' * (x_ - x)

TOTAL_SATS = 32

class RINEXFile:
    def __init__(self, filename):
        with open(expanduser(filename), 'r') as f:
          self._read_header(f)
          self._read_data(f)

    def save_hdf5(self, filename, append=True): #this can hard crash Python on some setups
        h5 = pandas.HDFStore(expanduser(filename), 'a' if append else 'w')
        h5[self.marker_name] = self.data
        h5.close()

    def save_pickle(self,filename): #last resort for those having HDF5 trouble
        fp = splitext(expanduser(filename))
        self.data.to_pickle(''.join((fp[0],'_',str(self.marker_name),fp[1])))


    def _read_header(self, f):
        version_line = padline(f.readline(), 80)

        self.version = float(version_line[0:9])
        if (self.version > 2.11):
            raise ValueError("RINEX file versions > 2.11 not supported (file version %f)" % self.version)

        self.filetype = version_line[20]
        if self.filetype not in "ONGM": # Check valid file type
            raise ValueError("RINEX file type '%s' not supported" % self.filetype)
        if self.filetype != 'O':
            raise ValueError("Only 'OBSERVATION DATA' RINEX files are currently supported")

        self.gnss = version_line[40]
        if self.gnss not in " GRSEM": # Check valid satellite system
            raise ValueError("Satellite system '%s' not supported" % self.filetype)
        if self.gnss == ' ':
            self.gnss = 'G'
        if self.gnss != 'G':
            #raise ValueError("Only GPS data currently supported")
            pass

        self.comment = ""
        while True: # Read the rest of the header
            line = padline(f.readline(), 80)
            label = line[60:80].rstrip()
            if label == "END OF HEADER":
                break
            if label == "COMMENT":
                self.comment += line[:60] + '\n'
            if label == "MARKER NAME":
                self.marker_name = line[:60].rstrip()
                if self.marker_name == '':
                  self.marker_name = 'UNKNOWN'
            if label == "# / TYPES OF OBSERV":
                n_obs = int(line[:6])
                self.obs_types = self._read_by_len(line[10:60],n_obs)
                while len(self.obs_types)<n_obs: #in case more than one obs_type line (more than 9 obs_types)
                    line = padline(f.readline(), 80)
                    self.obs_types.extend(self._read_by_len(line[10:60],n_obs))

    def _read_by_len(self,s,n_obs): #this could be done better with itertools
        return [s[6*i:2+6*i] for i in range(n_obs) if s[6*i:2+6*i].strip()]

    def _read_epoch_header(self, f):
        epoch_hdr = f.readline()
        if epoch_hdr == '':
            return None

        year = int(epoch_hdr[1:3])
        if year >= 80:
            year += 1900
        else:
            year += 2000

        epoch = datetime.datetime(year,
                                  month= int(epoch_hdr[4:6]),
                                  day  = int(epoch_hdr[7:9]),
                                  hour = int(epoch_hdr[10:12]),
                                  minute=int(epoch_hdr[13:15]),
                                  second=int(epoch_hdr[15:18]),
                                  microsecond=int(epoch_hdr[19:25])  # Discard the least sig. fig. (use microseconds only).
                                  )

        flag = int(epoch_hdr[28])
        if flag != 0:
            raise ValueError("Don't know how to handle epoch flag %d in epoch header:\n%s", (flag, epoch_hdr))

        n_sats = int(epoch_hdr[29:32])
        sats = []
        for i in range(0, n_sats):
            if ((i % 12) == 0) and (i > 0):
                epoch_hdr = f.readline()
            sats.append(epoch_hdr[(32+(i%12)*3):(35+(i%12)*3)])

        return epoch, flag, sats

    def _read_obs(self, f, n_sat, sat_map):
        obs = np.empty((TOTAL_SATS, len(self.obs_types)), dtype=np.float64) * np.NaN
        lli = np.zeros((TOTAL_SATS, len(self.obs_types)), dtype=np.uint8)
        signal_strength = np.zeros((TOTAL_SATS, len(self.obs_types)), dtype=np.uint8)

        for i in range(n_sat):
            # Join together observations for a single satellite if split across lines.
            obs_line = ''.join(padline(f.readline()[:-1], 16) for _ in range((len(self.obs_types) + 4) // 5))

            for j in range(len(self.obs_types)):
                obs_record = obs_line[16*j:16*(j+1)]
                obs[sat_map[i], j] = floatornan(obs_record[:14])
                lli[sat_map[i], j] = digitorzero(obs_record[14:15])
                signal_strength[sat_map[i], j] = digitorzero(obs_record[15:16])

        return obs, lli, signal_strength

    def _read_data_chunk(self, f, CHUNK_SIZE = 10000):
        obss = np.empty((CHUNK_SIZE, TOTAL_SATS, len(self.obs_types)), dtype=np.float64) * np.NaN
        llis = np.zeros((CHUNK_SIZE, TOTAL_SATS, len(self.obs_types)), dtype=np.uint8)
        signal_strengths = np.zeros((CHUNK_SIZE, TOTAL_SATS, len(self.obs_types)), dtype=np.uint8)
        epochs = np.zeros(CHUNK_SIZE, dtype='datetime64[us]')
        flags = np.zeros(CHUNK_SIZE, dtype=np.uint8)

        i = 0
        while True:
            hdr = self._read_epoch_header(f)
            #print hdr
            if hdr is None:
                break
            epoch, flags[i], sats = hdr
            epochs[i] = np.datetime64(epoch)
            sat_map = np.ones(len(sats)) * -1
            for n, sat in enumerate(sats):
                if sat[0] == 'G':
                    sat_map[n] = int(sat[1:]) - 1
            obss[i], llis[i], signal_strengths[i] = self._read_obs(f, len(sats), sat_map)
            i += 1
            if i >= CHUNK_SIZE:
                break

        return obss[:i], llis[:i], signal_strengths[:i], epochs[:i], flags[:i]

    def _read_data(self, f):
        obs_data_chunks = []

        while True:
            obss, llis, signal_strengths, epochs, flags = self._read_data_chunk(f)

            if obss.shape[0] == 0:
                break

            obs_data_chunks.append(pandas.Panel(
                np.rollaxis(obss, 1, 0),
                items=['G%02d' % d for d in range(1, 33)],
                major_axis=epochs,
                minor_axis=self.obs_types
            ).dropna(axis=0, how='all').dropna(axis=2, how='all'))

        self.data = pandas.concat(obs_data_chunks, axis=1)


def main():
    #import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="the RINEX file to process")
    parser.add_argument("output",
                        help="the output HDF5 file name")
    parser.add_argument("-n", "--marker-name", default=None,
                        help="override RINEX marker name")
    parser.add_argument("-I", "--info",
                        help="print information about the RINEX file",
                        action="store_true")
    args = parser.parse_args()

    rf = RINEXFile(args.input)

    if args.info:
        if args.marker_name is None:
            print("Marker Name:", rf.marker_name)
        else:
            print("Marker Name: %s (overriden, was %s)" % (args.marker_name, rf.marker_name))
        print("RINEX Version:", rf.version)
        if rf.comment != '':
            print("Comment:")
            print(rf.comment)
        print("Obervation types:", ', '.join(rf.data.axes[2]))
        print("Satellites:", ', '.join(rf.data.axes[0]))
        print("Total %d observations:\n\tfrom\t%s\n\tto\t%s" % \
            (len(rf.data.axes[1]), rf.data.axes[1][0], rf.data.axes[1][-1]))

    if args.marker_name is not None:
        rf.marker_name = args.marker_name

    rf.save_hdf5(args.output)

if __name__ == '__main__':
    main()

