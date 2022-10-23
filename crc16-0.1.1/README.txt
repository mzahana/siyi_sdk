====================================
Python library for calculating CRC16
====================================

CRC is a way of detecting accidental changes in data storage or
transmission.  There are many variants of CRC and CRC16, in particular.
This library calculates only CRC16 (16-bit codes) and the only supported
variant at the moment is CRC-CCITT (XModem).

If you want to know more about CRC,
http://wikipedia.org/wiki/Cyclic_redundancy_check is a good place to start.

If you want other variants of CRC16 supported, please make a request at
http://code.google.com/p/pycrc16/issues

Source codes are hosted at https://github.com/gennady/pycrc16
If you want to contribute to this library, create a fork, make you changes
and then create a pull request.  Any help is appreciated.

------------
Installation
------------

On Windows you can use precompiled binaries which can be found at
http://code.google.com/p/pycrc16/downloads

On Linux and other operation systems you should compile the library from
the source codes.  To do this on Linux use following steps:

* download source tarball, e.g. crc16-0.1.1.tar.gz,
  from http://code.google.com/p/pycrc16/downloads

* extract it with command::

    tar -xzf crc16-0.1.1.tar.gz

* compile and install the library::

    cd crc16-0.1.1
    python setup.py build
    sudo python setup.py install

  you will need the administrative privileges to execute the last
  command.

After installation you can run unit tests to make sure that the library
works fine.  Execute::

  python -m crc16.test

-----
Usage
-----

In Python 3::

    import crc16
    print(crc16.crc16xmodem(b'123456789'))

In Python 2 you should use strings instead of binary data::

    import crc16
    print(crc16.crc16xmodem('123456789'))

You can also calculate CRC gradually::

    import crc16
    crc = crc16.crc16xmodem(b'1234')
    crc = crc16.crc16xmodem(b'56789', crc)
    print(crc)

--------------
Other projects
--------------

There are a number of projects and libraries for CRC calculation.
See for example:

* binascii.crc32 in the standart Python library

* pycrc (http://www.tty1.net/pycrc)

* crcmod (http://pypi.python.org/pypi/crcmod)
