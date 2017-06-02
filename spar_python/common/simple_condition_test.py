# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for SimpleCondition 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  04 Apr 2012   omd            Original Version
# *****************************************************************


import unittest
import threading
from simple_condition import SimpleCondition
import time

class SimpleConditionTest(unittest.TestCase):
    def test_simple_bool(self):
        cond = SimpleCondition(False)
        self.assertEqual(cond.get(), False)

        def set_true():
            time.sleep(0.5)
            cond.set(True)

        threading.Thread(target = set_true).start()

        cond.wait(True)
        self.assertEqual(cond.get(), True)

    def test_simple_integer(self):
        cond = SimpleCondition(10)
        self.assertEqual(cond.get(), 10)

        # If we wait until its 10 and its already 10 it should return
        # immediately.
        cond.wait(10)
        self.assertEqual(cond.get(), 10)

        def set_true():
            time.sleep(0.5)
            cond.set(50)
            time.sleep(0.5)
            cond.set(100)

        threading.Thread(target = set_true).start()

        # When condition gets set to 50 this should not be released but it
        # should when it gets set to 100
        cond.wait(100)
        self.assertEqual(cond.get(), 100)

