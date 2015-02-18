#!/usr/bin/env python

# Copyright (C) 2014 Swift Navigation Inc.
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import pandas
import numpy as np

def epochpairs(a, b):
    ia = a.data.items
    ib = b.data.items
    pairs = []
    while len(ia) > 0 and len(ib) > 0:
        if abs(ia[0] - ib[0]) < timedelta(seconds=300e-3):
            #print ia[0], ' -- ', ib[0], ' (Delta: %.2f)' % ((ia[0] - ib[0]).total_seconds()*1e3)
            pairs.append((ia[0], ib[0]))
            ia = ia[1:]
            ib = ib[1:]
        elif ia[0].to_pydatetime() < ib[0].to_pydatetime():
            ia = ia[1:]
        else:
            ib = ib[1:]
    return pairs

def propagate(a, b):
    pairs = epochpairs(a, b)
    ia, ib = map(list, zip(*pairs))

    a_ = a.data.ix[ia,:,:]
    b_ = b.data.ix[ib,:,:]
    dt = array([(ta - tb).total_seconds() for ta, tb in pairs])
    b_.items = ia

    b_.ix[:, :, 'C1'] -= b_.ix[:, :, 'D1'].mul(dt*0.190293673) # Multiply by wavelength to convert to distance
    b_.ix[:, :, 'L1'] += b_.ix[:, :, 'D1'].mul(dt)

    return a_, b_

def sds(a, b):
    a_, b_ = a, b #propagate(a, b)
    sd = a_.transpose(1,0,2).sub(b_.transpose(1,0,2)).transpose(1,0,2)

    if 'snr' in sd.axes[1]:
      j = a_.transpose(1,0,2).join(b_.transpose(1,0,2), lsuffix='1', rsuffix='2').transpose(1,0,2)
      sd.ix[:,'snr', :] = j.ix[:,['snr1','snr2'],:].min(axis=1,skipna=False)
    if 'S1' in sd.axes[2]:
      sd = sd.drop('S1', axis=2)
    if 'S2' in sd.axes[2]:
      sd = sd.drop('S2', axis=2)

    return sd.dropna(how='all', axis=1).dropna(how='all', axis=0)

def sds_with_lock_counts(a, b):
    """
    Turn two panels of observations into a single differenced panel
    that includes lock counters.

    Paremeters
    ----------
    a : Panel
      An Panel of observations from one receiver.
    b : Panel
      An Panel of observations from another receiver.

    Returns
    -------
    Panel
      A panel of a's observations minus b's observations with a and b's lock
      counters and snrs.
    """
    a_, b_ = a, b #propagate(a, b)
    j = a_.transpose(1,0,2).join(b_.transpose(1,0,2), lsuffix='1', rsuffix='2').transpose(1,0,2)
    sd = sds(a, b)
    return sd.ix[:, [item for item in sd.major_axis if item != 'lock'], :]. \
          transpose(1,0,2).join(
              j.ix[:, ['lock1', 'lock2'], :].transpose(1,0,2)
          ).transpose(1,0,2)

def dds(a, b, ref, zero_ambs=False):
    sd = sds(a, b)
    dd = sd.sub(sd.ix[ref, :, :], axis=0)
    dd = dd.drop(ref, axis=0)
    dd = dd.rename_axis(lambda s: s + ' - ' + ref, axis=0)
    if zero_ambs:
      dd.ix[:, :, 'L1'] = dd.ix[:, :, 'L1'].sub(dd.ix[:, :, 'L1'].mean(axis=1).map(round), axis=0)
    return dd


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="the HDF5 file to process")
    parser.add_argument("base_name", default=False,
                        help="the marker name of the base station")
    parser.add_argument("rover_name", default=False,
                        help="the marker name of the rover")
    parser.add_argument("-r", "--reference",
                        help="choose reference satellite (defaults to highest mean SNR)")
    parser.add_argument("-v", "--verbose",
                        help="print more debugging information",
                        action="store_true")
    args = parser.parse_args()

    h5 = pandas.HDFStore(args.input)

    if args.reference is None:
      mean_snrs = h5[args.rover_name].ix[:, :, 'S1'].mean(axis=0)
      ref = mean_snrs.argmax()
    else:
      ref = args.reference

    if args.verbose:
      print "Using reference:", ref

    sd_table_name = 'sd_%s_%s' % (args.rover_name, args.base_name)
    if args.verbose:
      print
      print "Writing table '%s' of single differences:" % sd_table_name
      print
    h5[sd_table_name] = sds(h5[args.rover_name], h5[args.base_name])
    if args.verbose:
      print str(h5[sd_table_name])
      print

    dd_table_name = 'dd_%s_%s' % (args.rover_name, args.base_name)
    if args.verbose:
      print
      print "Writing table '%s' of double differences:" % dd_table_name
      print
    h5[dd_table_name] = dds(h5[args.rover_name], h5[args.base_name], ref)
    if args.verbose:
      print h5[dd_table_name]
      print

    h5.close()

if __name__ == '__main__':
    main()


