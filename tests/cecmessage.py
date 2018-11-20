"""
..
   This file is part of the CEC Control plugin.
   Copyright (C) 2018 Michael N. Lipp
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

.. moduleauthor:: mnl
"""

import unittest
from CecCtrl.cec import CecMessage


class Test(unittest.TestCase):


    def testVersion(self):
        self.assertEqual(CecMessage(0, 0, 0x9e, [5]).to_string(), 
                         "0->0: 9E 05 <CEC Version>  Version: 1.4")

    def testAbort(self):
        self.assertEqual(CecMessage(0, 0, 0, [0]).to_string(), 
                         "0->0: 00 00 <Feature Abort> Unrecognized opcode")

    def testPower(self):
        self.assertEqual(CecMessage(0, 0, 0x90, [1]).to_string(), 
                         "0->0: 90 01 <Report Power Status> (Standby)")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()