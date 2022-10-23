#!/usr/bin/env python3

##############################################################################
#
#    Copyright (C) Gennady Trafimenkov, 2010
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

from crc16 import _crc16
from crc16 import crc16pure
import crc16
import unittest

class TestCRC16XModem(unittest.TestCase):
    """Test CRC16 CRC-CCITT (XModem) variant.
    """


    def doBasics(self, module):
        """Test basic functionality.
        """
        # very basic example
        self.assertEqual(module.crc16xmodem(b'123456789'), 0x31c3)
        self.assertNotEqual(module.crc16xmodem(b'123456'), 0x31c3)

        # the same in two steps
        crc = module.crc16xmodem(b'12345')
        crc = module.crc16xmodem(b'6789', crc)
        self.assertEqual(crc, 0x31C3)

        # more basic checks
        self.assertEqual(module.crc16xmodem(b'AAAAAAAAAAAAAAAAAAAAAA'), 0x92cd)

        # bigger chunks
        self.assertEqual(module.crc16xmodem(b'A' * 4096), 0xd694)
        self.assertEqual(module.crc16xmodem(b'A' * 39999), 0xcfbb)

        # test when there are no data
        self.assertEqual(module.crc16xmodem(b''), 0)


    def test_basics(self):
        """Test basic functionality.
        """
        self.doBasics(crc16)


    def test_basics_c(self):
        """Test basic functionality of the extension module.
        """
        self.doBasics(_crc16)


    def test_basics_pure(self):
        """Test basic functionality of the pure module.
        """
        self.doBasics(crc16pure)


    def test_big_chunks(self):
        """Test calculation of CRC on big chunks of data.
        Test only the extension module becase the pure one will work very long for these tests.
        """
        self.assertEqual(_crc16.crc16xmodem(b'A' * 16 * 1024 * 1024), 0xbf75)


if __name__ == '__main__':
    unittest.main()
