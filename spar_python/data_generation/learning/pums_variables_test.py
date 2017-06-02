# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit test for the code in pums_variables.py 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  07 Dec 2011   omd            Original Version
# *****************************************************************

import unittest
from spar_python.common.enum import Enum
import spar_python.data_generation.learning.pums_variables as pv
import spar_python.data_generation.spar_variables as sv

class EnumParserManipulatorTest(unittest.TestCase):
    """Tests for the parser/mainpulator pair for enums."""
    def test_state_parsing(self):
        """State in an enum field in the PUMS data so we check that it parses
        correctly.

        State comes from the household record, not the person record. We use it
        for our parse test because its easy to verify correctness since the
        census bureau puts all the data for a state in the same file. Luckily
        state is in the middle of the row so it really does need to be
        parsed."""
        r_colorado = (
            'H000004550848001030810229952995999799972370    5675582368'
            '5655488838  143696518084  1433240289944700300100000300606'
            '01030101010101011 0 0 0030010000100001000110390020 0     '
            '0 0     0 0000 0    0    0  0 0    '
            '0400000000000440000000001041503921100000001242000000000')
        ret = sv.STATE_PARSER.parse(r_colorado)
        self.assertEqual(ret, 8)
        self.assertEqual(sv.STATE_MANIPULATOR.to_string(ret), 'Colorado')

        r_virginia = (
            'H000038855135031005109057205720572057202323    '
            '2171576501    1940023957    3329827682   '
            '2961636509540017010000030060702050301010101000 '
            '0 0 0000000000000000000100440020 0     0 0     0 '
            '0000 0    0    0  0 0    '
            '0600000000000440000000001044003221100000001650000000000')
        ret = sv.STATE_PARSER.parse(r_virginia)
        self.assertEqual(ret, 51)
        self.assertEqual(sv.STATE_MANIPULATOR.to_string(ret), 'Virginia')

    def test_remap_enum_parser(self):
        """Tests for RemapEnumParser."""
        e = Enum(A = 1, B = 5, C = 9)
        # Map [2,5) => 'A' and [6, 9) => 'C'
        parser = pv.RemapEnumParser(
                ((range(2, 5), e.A), (range(6, 9), e.C)),
                e, 5, 6)

        self.assertEqual(parser.parse('PJUNK1JUNK'), e.A)
        self.assertEqual(parser.parse('PJUNK3JUNK'), e.A)
        self.assertEqual(parser.parse('PJUNK4JUNK'), e.A)

        self.assertEqual(parser.parse('PJUNK5JUNK'), e.B)

        self.assertEqual(parser.parse('PJUNK6JUNK'), e.C)
        self.assertEqual(parser.parse('PJUNK9JUNK'), e.C)
