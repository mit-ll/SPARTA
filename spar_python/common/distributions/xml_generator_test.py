# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Tests for XML generator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  03 Oct 2013   jch            Original Version
# *****************************************************************
from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import unittest
import time
import StringIO as stringio
import logging
import xml.etree.ElementTree as ElementTree
import collections

from spar_python.common.distributions.xml_generator import \
    (XmlGenerator, GeneratedXml)
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import spar_python.data_generation.spar_variables as sv
import spar_python.common.distributions.distribution_holder as dh
import spar_python.common.spar_random as spar_random
import spar_python.data_generation.learn_distributions as learn_distributions


                   
                   
class GeneratedXmlTest(unittest.TestCase):
    
    def setUp(self):
        
        root = ElementTree.Element('a')
        root.text = 'A node text'
        b = ElementTree.SubElement(root, 'b')
        c = ElementTree.SubElement(root, 'c')
        c.text = 'C node text'
        d = ElementTree.SubElement(b, 'd')
        d.text = 'D node text'
        f = ElementTree.SubElement(b, 'f')
        f.text = 'F node text'
        etree = ElementTree.ElementTree(root)
        self.generated_xml = GeneratedXml(etree)

        
    def test_str(self):

        goal_str = "<a>A node text<b><d>D node text</d><f>F node text</f></b><c>C node text</c></a>"
                
        generated_str = str(self.generated_xml)
        self.assertEqual(generated_str, goal_str)   

        generated_str = self.generated_xml.str()
        self.assertEqual(generated_str, goal_str)   
                   
    def test_len(self):
        
        self.assertEqual(len(self.generated_xml), 79)
                   
                   
    def test_match_xpath(self):
        
        matching_xpath_expressions = ['.',
                                      './b',
                                      './c',
                                      './b/d',
                                      './b/f',
                                      './/f']
        for expression in matching_xpath_expressions:
            self.assertTrue(
                self.generated_xml.matches_xpath_expression(expression),
                expression)
                   
                
        invalid_xpath_expressions = ['a/b/g',
                                     './/g']
        for expression in invalid_xpath_expressions:
            self.assertFalse(
                self.generated_xml.matches_xpath_expression(expression),
                expression)
            
    def test_has_leaf(self):
        
        yes_pairs = [('c', 'C NODE TEXT'),
                     ('d', 'D NODE TEXT'),
                     ('f', 'F NODE TEXT')]
        
        for (yes_tag, yes_value) in yes_pairs:
            result = self.generated_xml.has_leaf(yes_tag, yes_value)
            self.assertTrue(result, (yes_tag, yes_value))
            
        no_pairs = [('b', 'c node text'),
                    ('C', 'c node text'),
                    ('d', 'c node text'),
                    ('a', 'a node text')]
        
        for (no_tag, no_value) in no_pairs:
            result = self.generated_xml.has_leaf(no_tag, no_value)
            self.assertFalse(result)


    def test_has_path (self):
        
        yes_pairs = [( ['a', 'c'], 'C NODE TEXT'),
                     ( ['a', 'b', 'd'], 'D NODE TEXT'),
                     ( ['a', 'b', 'f'], 'F NODE TEXT')]
        
        for (yes_tag_list, yes_value) in yes_pairs:
            result = self.generated_xml.has_path(yes_tag_list, yes_value)
            self.assertTrue(result)
            
        no_pairs = [( ['a'], 'c node text'),
                    ( ['a', 'B', 'd'], 'd node text'),
                    ( ['a', 'b', 'c'], 'c node text'),
                    ( ['c'], 'c node text'),
                    ( ['a', 'd'], 'd node text'),
                    ( ['a', 'b'], 'f node text')]
        
        for (no_tag_list, no_value) in no_pairs:
            result = self.generated_xml.has_path(no_tag_list, no_value)
            self.assertFalse(result)

           
# Note: need this to make mock options
class Options(object):
    pass


class XmlGeneratorTest(unittest.TestCase):

    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

        self.dummy_logger = logging.getLogger('dummy')
        self.dummy_logger.addHandler(logging.NullHandler())

        learner_options = Options()
        learner_options.verbose = False

        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(learner_options,
                                                 self.dummy_logger,
                                                 pums_files)
            
        names_files = \
            [('male_first_names.txt', 
              stringio.StringIO(mock_data_files.mock_male_first_names)),
             ('female_first_names.txt', 
              stringio.StringIO(mock_data_files.mock_female_first_names)),
             ('last_names.txt', 
              stringio.StringIO(mock_data_files.mock_last_names))]
        names_dict = \
            learn_distributions.learn_name_dists(learner_options,
                                                 self.dummy_logger,
                                                 names_files)

        vars = [sv.VARS.SEX,
                sv.VARS.CITIZENSHIP,
                sv.VARS.AGE,
                sv.VARS.RACE,
                sv.VARS.STATE,
                sv.VARS.FIRST_NAME,
                sv.VARS.LAST_NAME]

        var_order = vars
        var_names = [sv.VARS.to_string(x) for x in vars]
        dist_dict = { }
        dist_dict.update(pums_dict)
        dist_dict.update(names_dict)
        
        self.dist_holder = dh.DistributionHolder(var_order, var_names, dist_dict)


        
    def test_generate(self):

        xml_gen = XmlGenerator(self.dist_holder)

        for _ in xrange(200):
        
            xml = xml_gen.generate()
            etree = xml.to_etree().getroot()
        
            self.assertEqual(etree.tag, 'xml')
        
            children = list(etree)
            self.assertEqual(len(children), 5)
        
            for child in children:
                
                self.assertIn(child.tag, ['a0', 'a1', 'a2', 'a3', 'a4', 'a5',
                                          'a6', 'a7', 'a8', 'a9', 'a10'])

                grandchildren = list(child)
                self.assertEqual(len(grandchildren), 5)

                for grandchild in grandchildren:
                    
                    self.assertIn(grandchild.tag, ['b0', 'b1', 'b2', 'b3', 'b4', 
                                                   'b5','b6', 'b7', 'b8', 'b9', 
                                                   'b10'])

                    leaves = list(grandchild)
                    self.assertEqual(len(leaves), 5)
                    
                    leaf_set = set([leaf.tag for leaf in leaves])
                    self.assertEqual(len(leaf_set), 5)
                    # For sets, s1 <= s2 means 's1 is a subset of s2"
                    self.assertLessEqual(leaf_set, 
                                         set(['fname', 'lname', 'sex', 'age',
                                              'citizenship', 'race', 'state']))
                        
        
    def test_str(self):
        xml_gen = XmlGenerator(self.dist_holder)
        xml = xml_gen.generate()
        
        xml_str = str(xml)

        self.assertTrue(xml_str.startswith('<xml>'))
        self.assertTrue(xml_str.endswith('</xml>'))

        # Does the text parse?
        root = ElementTree.fromstring(xml_str)


    def test_check_forbidden_characters(self):
        
        xml_gen = XmlGenerator(self.dist_holder)

        # The following should not raise exceptions
        xml_gen.check_forbidden_characters(['$', "*", "!"])
        
        # The following characters should raise exceptions
        bad_characters = ["<", "/", "x", "a", "b", "f"]
        for bad_char in bad_characters:
            with self.assertRaises(AssertionError): 
                xml_gen.check_forbidden_characters([bad_char])
            
        
        
        

                