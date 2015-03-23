#!/usr/bin/env python3
from __future__ import absolute_import, print_function, division
from pynex.rinex_file import RINEXFile
from os.path import expanduser,splitext
from pandas.io.pickle import read_pickle
from matplotlib.pyplot import figure,show

def demorinex(rinexfn):
    #switchyard based on filename extension
    name,ext = splitext(rinexfn)[1]
    if ext[-1] == 'o':
        f = RINEXFile(rinexfn)
        f.data.to_pickle(name + '.pickle')
        return f
    elif ext in ('.pkl','.pickle'):
        return read_pickle(expanduser(rinexfn))

def plotdata(data):
    sc = ('L1','L2')
    startdate = data.major_axis[0].strftime('%Y-%m-%d')
    for s in sc:
        ax = figure().gca()
        for i in data.items:
            ax.plot(data[i].index,data[i][s])

        ax.set_title(startdate + ' SV {:s} - {:s}: {:s}'.format(data.items[0], data.items[-1], s))

    show()

if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser(description='demonstration of reading a RINEX 2 file')
    p.add_argument('rinexfn',help='pathname of RINEX file',type=str)
    p.add_argument('--profile',help='debug of code via profiling',action='store_true')
    p = p.parse_args()

    if not p.profile:
        data = demorinex(p.rinexfn)
        plotdata(data)
    else:
        import cProfile
        from pstats import Stats
        proffn = 'rinprof_old.pstats'
        cProfile.run('demorinex(p.rinexfn)',proffn)
        p = Stats(proffn)
        p.sort_stats('time','cumulative').print_stats(50)

