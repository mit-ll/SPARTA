
# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for generated_row.py
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  4 Nove 2013   jch            Original version
# ***********************************************************
import unittest
import datetime
import xml.etree.ElementTree as ElementTree


import spar_python.data_generation.spar_variables as sv
import spar_python.data_generation.generated_row as generated_row
from spar_python.common.distributions.generated_text import GeneratedText
from spar_python.common.distributions.xml_generator import \
    (XmlGenerator, GeneratedXml)



class GeneratedRowTest(unittest.TestCase):


    def setUp(self):
        
        self.generated_row = generated_row.GeneratedRow()
        
        
    def test_tabula_rasa(self):
        
        self.assertDictEqual(self.generated_row, {})
        self.assertDictEqual(self.generated_row.in_query_aggregator_format, {})
        
        
    def test_add_int_variable(self):
        
        income_field = sv.VARS.INCOME
        self.generated_row[income_field] = 10
        
        self.assertEqual(self.generated_row[income_field], 10)
        self.assertEqual(self.generated_row.in_query_aggregator_format[income_field],
                         10)
        
        
    def test_add_enum_variable(self):
        
        state_field = sv.VARS.STATE
        self.generated_row[state_field] = sv.STATES.Maine
        
        self.assertEqual(self.generated_row[state_field], sv.STATES.Maine)
        self.assertEqual(self.generated_row.in_query_aggregator_format[state_field],
                         'MAINE')
        
        
        
    def test_add_string_variable(self):
        
        fname_field = sv.VARS.FIRST_NAME
        self.generated_row[fname_field] = "Jonathan"
        
        self.assertEqual(self.generated_row[fname_field], 'Jonathan')
        self.assertEqual(self.generated_row.in_query_aggregator_format[fname_field],
                         'JONATHAN')
        
        
    def test_add_byte_array_variable(self):
        fingerprint_field = sv.VARS.FINGERPRINT
        self.generated_row[fingerprint_field] = bytearray(range(65, 91))
        
        self.assertEqual(self.generated_row[fingerprint_field], 
                         bytearray(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        self.assertEqual(self.generated_row.in_query_aggregator_format[fingerprint_field],
                         '4142434445464748494a4b4c4d4e4f505152535455565758595a')
    
    def test_add_dob_variable(self):
        dob_field = sv.VARS.DOB
        self.generated_row[dob_field] = datetime.date(2013,1,1)
        
        self.assertEqual(self.generated_row[dob_field], 
                         datetime.date(2013,1,1))
        self.assertEqual(self.generated_row.in_query_aggregator_format[dob_field],
                         datetime.date(2013,1,1))
        
    
    def test_add_test_variable(self):
        notes_field = sv.VARS.NOTES4
        
        word_list = ['It', ' ', 'was', ' ', 'the', ' ', 'best', ' ', 'of', ' ', 'times', '.']
        stem_list = ['it', None, 'was', None, 'the', None, 'best', None, 'of', None, 'time', None]
        lower_word_list = [word.lower() for word in word_list]
        generated_text = GeneratedText(word_list,
                                       stem_list,
                                       lower_word_list)

        
        self.generated_row[notes_field] = generated_text
        
        self.assertEqual(self.generated_row[notes_field], 
                         generated_text)
        self.assertEqual(self.generated_row.in_query_aggregator_format[notes_field],
                         'it was the best of times.')


    def test_xml_variable(self):
        xml_field = sv.VARS.XML
        
        root = ElementTree.Element('a')
        b = ElementTree.SubElement(root, 'b')
        c = ElementTree.SubElement(root, 'c')
        _ = ElementTree.SubElement(b, 'd')
        _ = ElementTree.SubElement(b, 'f')
        etree = ElementTree.ElementTree(root)
        generated_xml = GeneratedXml(etree)

        
        self.generated_row[xml_field] = generated_xml
        
        self.assertEqual(self.generated_row[xml_field], 
                         generated_xml)
        self.assertEqual(self.generated_row.in_query_aggregator_format[xml_field],
                         generated_xml)
    