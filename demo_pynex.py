#!/usr/bin/env python3
from __future__ import absolute_import, print_function, division
from pynex.rinex_file import RINEXFile
from os.path import expanduser,splitext
from pandas.io.pickle import read_pickle
from matplotlib.pyplot import figure,show
from numpy import empty

def demorinex(obsfn,maxchunk=None):
    #switchyard based on filename extension
    name,ext = splitext(obsfn)
    if ext[-1] == 'o':
        f = RINEXFile(obsfn,maxchunk)
        f.save_pickle(name + '.pickle')
        f.save_hdf5(name+'.h5') #this can crash some Python with incompatible PyTables/Pandas/HDF5 versions
        return f.data
    elif ext in ('.pkl','.pickle'):
        return read_pickle(expanduser(obsfn))
    elif ext in ('.h5','.hdf5'):
        print('not implemented yet')
        return None

def plotdata(data):
    if data is None: return

    sc = ('L1','L2','C1')
    yl = ('carrier phase (cycles)','carrier phase (cycles)','pseudorange (meters)')
    startdate = data.major_axis[0].strftime('%Y-%m-%d')
    for q,l in zip(sc,yl):
        ax1 = figure().gca()
        for i,sat in data.iteritems():
            try:
                ax1.plot(sat.index, sat[q], label=i)
            except IndexError:
                break
        ax1.set_title(startdate + ' SV {} - {}: {}'.format(data.items[0], data.items[-1], q))
        ax1.set_xlabel('time')
        ax1.set_ylabel(l)
    
    ax2 = figure().gca()
    for i,s in data.iteritems():
        ax2.plot(s.index, s['TECslp'])
    ax2.set_xlabel('time')
    ax2.set_ylabel('TEC')
    ax2.set_title(startdate + ' SV {} - {}:  TEC'.format(data.items[0], data.items[-1]))
    
def estimateTEC(data):
    """
    Implementation of Eqn. 1 from 
    G. Ma, T. Maruyama. Derivation of TEC and estimation of instrumental biases from GEONET
    in Japan. Annales Geophysicae, European Geosciences Union (EGU), 2003, 21 (10), pp.2083-2093
    """
    f1 = 1575.42e6 #[hz]
    f2 = 1227.60e6 #[hz]
    k = 80.62 #[m^3/s^2]
    data.ix[:,:,'TECslp'] = 2*(f1*f2)**2 / (k*(f1**2-f2**2)) * (data.ix[:,:,'P2'] -data.ix[:,:,'P1'])
    return data

if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser(description='demonstration of reading a RINEX 2 Observation file')
    p.add_argument('obsfn',help='pathname of RINEX Observation file',type=str)
    p.add_argument('--profile',help='debug of code via profiling',action='store_true')
    p.add_argument('-m','--maxchunk',help='how many chunks to read from start of file (default: whole file)',type=int,default=None)
    p = p.parse_args()

    if not p.profile:
        data = demorinex(p.obsfn, p.maxchunk)
        data = estimateTEC(data)
        plotdata(data)
        show()
    else:
        import cProfile
        from pstats import Stats
        proffn = 'rinprof_old.pstats'
        cProfile.run('demorinex(p.obsfn)',proffn)
        p = Stats(proffn)
        p.sort_stats('time','cumulative').print_stats(50)

