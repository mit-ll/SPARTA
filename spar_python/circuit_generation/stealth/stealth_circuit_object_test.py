# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Stealth TA2 circuit object superclass test
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  17 Oct 2012   SY             Original version
# *****************************************************************

import spar_python.circuit_generation.stealth.stealth_circuit_object as sco
import unittest

class TestCircuitObject(unittest.TestCase):

    def test_bad_init(self):
        """
        Tests that initializing a circuit object with a None, an integer,
        or an empty string as a displayname throws an error.
        """
        self.assertRaises(TypeError,
                          sco.StealthCircuitObject, None)
        self.assertRaises(TypeError,
                          sco.StealthCircuitObject, 1)
        self.assertRaises(AssertionError,
                          sco.StealthCircuitObject, "")
    
    def test_get_name(self):
        """
        Tests that get_name returns the name of the object correctly.
        """
        co1_name = "object1"
        co1 = sco.StealthCircuitObject(co1_name)
        self.assertEqual(co1.get_name(), co1_name)

    def test_get_short_display_string(self):
        """
        Tests that get_short_display_string returns the appropriate
        representation string.
        self.co1.get_short_display_string(x) where x can be interpreted as False
        (i.e. x = False, x = 0, etc) shoud give "object1",
        self.co1.get_short_display_string(x) where x can be interpreted as True
        (i.e. x = True, x = 1, etc) should give "N(object1)",
        and self.co1.get_short_display_string(x) where x is anything that is not
        equal to True or False should result in an AssertionError.
        """
        co1_name = "object1"
        co1 = sco.StealthCircuitObject(co1_name)
        self.assertEqual(co1.get_short_display_string(False),
                         "object1")
        self.assertEqual(co1.get_short_display_string(0),
                         "object1") 
        self.assertEqual(co1.get_short_display_string(True),
                         "N(object1)")
        self.assertEqual(co1.get_short_display_string(1),
                         "N(object1)") 
        self.assertRaises(AssertionError,
                          co1.get_short_display_string, None)
        self.assertRaises(AssertionError,
                          co1.get_short_display_string, "this_is_a_string") 
        
    def test_evaluate(self):
        """
        Tests to see that calling evaluate from a CircuitObject (and not from
        a subclass thereof) causes an AssertionError.
        """
        co1_name = "object1"
        co1 = sco.StealthCircuitObject(co1_name)
        self.assertRaises(AssertionError, co1.evaluate)

