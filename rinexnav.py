"""
Reads RINEX 2.1 NAV files
by Michael Hirsch
bostonmicrowave.com
GPLv3+
"""
from __future__ import division
from os.path import expanduser
import numpy as np
from datetime import datetime
from pandas import DataFrame

def readRINEXnav(fn):
    """
    Michael Hirsch
    It may actually be faster to read the entire file via f.read() and then .split()
    and asarray().reshape() to the final result, but I did it frame by frame.
    http://gage14.upc.es/gLAB/HTML/GPS_Navigation_Rinex_v2.11.html
    """
    n = 19 #num of characters per number
    startcol = 3 #column where numerical data starts
    numdat = 4 #number of data elements per line
    yb = 2000 # TODO I'm assuming it's the 21st century!

    with open(expanduser(fn),'r') as f:
        #find end of header, which has non-constant length
        while True:
            if 'END OF HEADER' in f.readline(): break
        #handle frame by frame
        sv = []; epoch=[]; raws=[]
        while True:
            headln = f.readline()
            if not headln: break # eof
            #handle the header
            sv.append(headln[:2])
            epoch.append(datetime(year =yb+int(headln[2:5]),
                                  month   =int(headln[5:8]),
                                  day     =int(headln[8:11]),
                                  hour    =int(headln[11:14]),
                                  minute  =int(headln[14:17]),
                                  second  =int(headln[17:20]),
                                  microsecond=int(headln[21])*100000))
            #now get the data
            raw = headln[22:-1]  #don't let the line return through!

            for i in range(7):
                raw += f.readline()[startcol:n*numdat+startcol]
            raws.append([raw[i:i+n].replace('D','E') for i in range(0,7*n*numdat+n,n)])

        darr = np.asarray(raws).astype(np.float64)

        nav= DataFrame(data = np.hstack((np.asarray(sv).astype(int)[:,None], darr)),
                         index=epoch,
                         columns=['sv','SVclockBias','SVclockDrift','SVclockDriftRate','IODE',
                                 'Crs','DeltaN','M0','Cuc','Eccentricity','Cus',
                                  'sqrtA','TimeEph','Cic','OMEGA','CIS','Io','Crc',
                                  'omega','OMEGA DOT','IDOT','CodesL2','GPSWeek',
                                  'L2Pflag','SVacc','SVhealth','TGD','IODC',
                                  'TransTime','FitIntvl'])

        return nav

if __name__ == '__main__':
    from sys import argv

    nav = readRINEXnav(argv[1])
