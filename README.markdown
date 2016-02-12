pyNEX
=====

Python RINEX utilities

Installation
------------

For dependencies:

    $ sudo bash deps.sh

Install:

    $ python setup.py install

Alternatively, if you are developing pyNEX and want to install a link to your working copy:

    $ python setup.py develop


Usage
-----

As well as being a library, pyNEX comes with two command line utilities.

`pynex` takes a RINEX file and outputs an HDF5 file that can be read by pandas.
The HDF5 file will have a table appended to it containing the observations
using the marker name as the table name.

    $ pynex --help
    usage: pynex [-h] [-n MARKER_NAME] [-I] input output

    positional arguments:
      input                 the RINEX file to process
      output                the output HDF5 file name

    optional arguments:
      -h, --help            show this help message and exit
      -n MARKER_NAME, --marker-name MARKER_NAME
                            override RINEX marker name
      -I, --info            print information about the RINEX file

`ddtool` takes an HDF5 file and two marker names and computes the single and
double difference observations, writing them back into the same HDF5 file.

    $ ddtool --help
    usage: ddtool [-h] [-r REFERENCE] [-v] input base_name rover_name

    positional arguments:
      input                 the HDF5 file to process
      base_name             the marker name of the base station
      rover_name            the marker name of the rover

    optional arguments:
      -h, --help            show this help message and exit
      -r REFERENCE, --reference REFERENCE
                            choose reference satellite (defaults to highest mean
                            SNR)
      -v, --verbose         print more debugging information

