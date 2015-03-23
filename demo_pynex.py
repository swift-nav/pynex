#!/usr/bin/env python3
from __future__ import absolute_import, print_function, division #making Python 2.7 behave more like Python 3
from pynex.rinex_file import RINEXFile

def demorinex(rinexfn):
    f = RINEXFile(rinexfn)
    return f

if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser(description='demonstration of reading a RINEX 2 file')
    p.add_argument('rinexfn',help='pathname of RINEX file',type=str)
    p = p.parse_args()

    data = demorinex(p.rinexfn)
