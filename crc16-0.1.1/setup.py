#!/usr/bin/env python
"""Setup script for crc16 library"""

##############################################################################
#
#    Copyright (C) Gennady Trafimenkov, 2011
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from distutils.core import setup, Extension
import os
import sys

if __name__ == '__main__':

    majorVer = int(sys.version_info[0])
    minorVer = int(sys.version_info[1])

    if majorVer >= 3:
        baseVersion = "python3x"
    else:
        if majorVer == 2 and minorVer >= 6:
            baseVersion = "python2x"
        else:
            baseVersion = "python25"

    readmePath = os.path.join(os.path.dirname(__file__), 'README.txt')
    long_description = open(readmePath, "rt").read()

    setup(name='crc16',
          version='0.1.1',
          description='Library for calculating CRC16',
          author='Gennady Trafimenkov',
          author_email='gennady.trafimenkov@gmail.com',
          url='http://code.google.com/p/pycrc16',
          license='LGPL',
          keywords=['CRC16'],
          packages=['crc16'],
          package_dir={'': baseVersion},
          ext_modules = [Extension('crc16._crc16', sources=['src/_crc16module.c']),
                         ],

          # get classifiers from here
          # http://pypi.python.org/pypi?:action=list_classifiers
          classifiers = [
            # "Development Status :: 1 - Planning",
            # "Development Status :: 2 - Pre-Alpha",
            "Development Status :: 3 - Alpha",
            # "Development Status :: 4 - Beta",
            # "Development Status :: 5 - Production/Stable",
            # "Development Status :: 6 - Mature",
            # "Development Status :: 7 - Inactive",

            # "Environment :: Other Environment",

            "Intended Audience :: Developers",
            "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",

            # "Operating System :: OS Independent",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX",

            "Topic :: Software Development :: Libraries :: Python Modules",

            # "Programming Language :: C",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.4",
            "Programming Language :: Python :: 2.5",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.1",
            "Programming Language :: Python :: 3.2",
            ],
          long_description=long_description
          )
