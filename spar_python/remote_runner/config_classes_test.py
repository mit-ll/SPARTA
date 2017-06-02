# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for ConfigClasses 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Jan 2013   omd            Original Version
# *****************************************************************

import config_classes
import unittest

class ConfigTestClass(config_classes.ConfigClassesBase):
    """A simple subclass of ConfigClassesBase the has attributes x and y."""
    LEGAL_ATTRS = set(['x', 'y'])
    def __init__(self, x):
        super(ConfigTestClass, self).__init__()
        self.x = x

class ConfigTestClass2(config_classes.ConfigClassesBase):
    """A simple subclass of ConfigClassesBase the has attributes x and y."""
    LEGAL_ATTRS = set(['a1', 'attribute2', 'bar', 'foo'])
    def __init__(self):
        super(ConfigTestClass2, self).__init__()

class TestConfigClasses(unittest.TestCase):
    def test_attribute_limitations(self):
        """Makes sure that subclasses of ConfigClassesBase can only have the
        attributes listed in LEGAL_ATTRS."""
        t = ConfigTestClass(10)
        self.assertEqual(t.x, 10)
        t.y = 100
        self.assertEqual(t.y, 100)
        with self.assertRaises(AttributeError):
            t.z = 90

    def test_all_set_works(self):
        t = ConfigTestClass(10)
        self.assertFalse(t.all_set())
        t.y = 90
        self.assertTrue(t.all_set())

    def test_get_missing_attrs_works(self):
        t = ConfigTestClass2()
        m = t.get_missing_attributes()
        m.sort()
        self.assertEqual(m, ['a1', 'attribute2', 'bar', 'foo'])

        t.foo = 100
        m = t.get_missing_attributes()
        m.sort()
        self.assertEqual(m, ['a1', 'attribute2', 'bar'])

        t.attribute2 = 'something else'
        m = t.get_missing_attributes()
        m.sort()
        self.assertEqual(m, ['a1', 'bar'])

        t.a1 = 'this is a1'
        t.bar = set()
        m = t.get_missing_attributes()
        m.sort()
        self.assertEqual(m, [])

