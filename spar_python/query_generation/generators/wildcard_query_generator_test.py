# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Tests for wildcard_query_generator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  22 August 2012  ATLH            Original version
# *****************************************************************

from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import unittest
import time
import wildcard_query_generator as wqg
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.base_distributions as base_distribution
import spar_python.common.distributions.text_generator as text_generator
import StringIO as s
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv
import spar_python.common.aggregators.query_aggregator as qa

match_fun = {'initial-one': qa.SearchInitialNumQA.is_match,
             'middle-one' : qa.SearchMultipleNumQA.is_match, 
             'final-one' : qa.SearchFinalNumQA.is_match,
             'final' : qa.P7FinalQA.is_match, 
             'initial' : qa.P7InitialQA.is_match,
             'both' : qa.P7BothQA.is_match }

class WildcardQueryGeneratorTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        #set up intitialization values 
        sub_cat = 'eq'
        self._dist1 = base_distribution.CompactIndependentDistribution()
        self._dist1.add('Letus',1)
        self._dist1.add('arbey', 9)
        self._dist1.add('Amelia', 1)
        self._dist1.add('Anfrew', 9)
        self._dist1.add('Roberts', 1)
        self._dist1.add('Andreas', 9)
        self._dist1.add('Vacation', 1)
        self._dist1.add('Occulary', 9)
        self._dist1.add('Fuzzballs', 1)
        self._dist1.add('Divasmuch', 9)
        self._dist1.add('tenletters', 1)
        self._dist1.add('arehardtoo', 9)
        self._dist1.add('elevenseven', 1)
        self._dist1.add('harderthant', 9)
        self._dist2 = base_distribution.CompactIndependentDistribution()
        self._dist2.add('Smith', 1)
        self._dist2.add('Henry', 9)
        self._dist2.add('Roberts', 1)
        self._dist2.add('Andreas', 9)
        self._dist2.add('Vacation', 1)
        self._dist2.add('Occulary', 9)
        self._dist2.add('Fuzzballs', 1)
        self._dist2.add('Divasmuch', 9)
        self._dist2.add('tenletters', 1)
        self._dist2.add('arehardtoo', 9)
        self._dist2.add('elevenseven', 1)
        self._dist2.add('harderthant', 9)
        f = s.StringIO('''A a b my spout, when you tip me over hear me a a b.
                C cc e I'm a little teacup short and stout, here is my c cc e. 
        F fff h something about something about something of something f fff h.
        I jjjj l sentence generation is hard and annoying when doing i jjjj l. 
        M nnnnn p lets try to include more original sentenctes what m nnnnn p.
        Q rrrrrr s interesting trial of things and other things that q rrrrrr s. 
        U vvvvvvv y and need to include some other stuff to make u vvvvvvv y.''')
        self._dist3 = text_generator.TextGenerator((f,))
        fields_non_notes = [sv.sql_name_to_enum('fname'), sv.sql_name_to_enum('lname')]
        fields_notes = [sv.sql_name_to_enum('notes1')]
        dists = [self._dist1,self._dist2]
        other_fields = ['no_queries','r_lower','r_upper','keyword_len','type']
        other_cols_P6 = [[2, 1, 100, 5,'initial-one'],[2, 1, 100, 9,'middle-one'],
                         [2, 1, 100, 5,'final-one']]
        other_cols_P7 = [[2, 1, 200, 5,'initial'], [2, 1, 250, 5,'both'],
                         [2, 1, 200, 5,'final']]
        self.P6_non_notes_generator = wqg.WildcardQueryGenerator('P6','', ["LL"],dists, fields_non_notes,
                                                                  1000, 100,other_fields, other_cols_P6)
        self.P7_non_notes_generator = wqg.WildcardQueryGenerator('P7','',["LL"], dists, fields_non_notes,
                                                                  1000, 100,other_fields, other_cols_P7)
        self.P7_notes_generator = wqg.WildcardQueryGenerator('P7','',["LL"], [self._dist3], fields_notes,
                                                            1000, 100,other_fields, other_cols_P7)
        
    def is_match(self, q, value):
        if q[qs.QRY_SUBCAT] in ['middle-one']:
            return match_fun[q[qs.QRY_SUBCAT]](q[qs.QRY_SEARCHFORLIST], 
                                            q[qs.QRY_SEARCHDELIMNUM],
                                            value)
        elif q[qs.QRY_SUBCAT] in ['final-one','initial-one']:
            return match_fun[q[qs.QRY_SUBCAT]](q[qs.QRY_SEARCHFOR], 
                                            q[qs.QRY_SEARCHDELIMNUM],
                                            value)
        else:
            # P7s
            return match_fun[q[qs.QRY_SUBCAT]](q[qs.QRY_SEARCHFOR],value)
        
        
    def testGenerateP6NonNotesQuery(self):     
        """
        Tests P6 functionality of query generator on non notes fields against 
        a 'db' to make sure it is generating the right queries
        """
        
        values1 = []
        values2 = []
        for _ in xrange(1000):
           values1.append(self._dist1.generate())
           values2.append(self._dist2.generate())

        #generate queries
        query_batches = self.P6_non_notes_generator.produce_query_batches()
        queries = []
        for query_batch in query_batches:
            queries += query_batch.produce_queries()
        #check to see right number of queries generated
        q_dist1 = 0
        q_dist2 = 0
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        for q in queries:
            self.assertEqual('P6', q[qs.QRY_CAT], self.seed_msg)
            if q[qs.QRY_FIELD] == 'fname':
                q_dist1 += 1
                value = values1
            elif q[qs.QRY_FIELD] == 'lname':
                q_dist2 += 1
                value = values2
            count_match = len([x for x in value if self.is_match(q,x)])
            msg = 'Query %d was: \n' \
                  'subcategory: %s\n'\
                  'field: %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'regular_expression: %s\n'\
                  'where_clause: %s\n' % (q[qs.QRY_QID], q[qs.QRY_FIELD], q[qs.QRY_SUBCAT], 
                                   q[qs.QRY_LRSS], q[qs.QRY_URSS],
                                   q[qs.QRY_SEARCHFOR], q[qs.QRY_WHERECLAUSE])
            self.assertLessEqual(count_match, q[qs.QRY_URSS]*2, msg)
            self.assertGreaterEqual(count_match, q[qs.QRY_LRSS]/2, msg)
        #check to see each field had the correct number of queries
        #ideally this number would be greater than 6 (the requested amount)
        #but because the distribution used for unit testing is so small
        #there is a greater margin of error at this scale
        self.assertGreaterEqual(q_dist1, 3, self.seed_msg)
        self.assertGreaterEqual(q_dist2, 3, self.seed_msg) 

        
    def testGenerateP7NonNotesQuery(self):     
        """
        Tests P7 functionality of query generator on non notes fields against 
        a 'db' to make sure it is generating the right queries
        """
        
        values1 = []
        values2 = []
        for _ in xrange(1000):
           values1.append(self._dist1.generate())
           values2.append(self._dist2.generate())
        #generate queries
        query_batches = self.P7_non_notes_generator.produce_query_batches()
        queries = []
        for query_batch in query_batches:
            queries += query_batch.produce_queries()
        
        #check to see right number of queries generated
        q_dist1 = 0
        q_dist2 = 0
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        for q in queries:
            self.assertEqual('P7', q[qs.QRY_CAT], self.seed_msg)
            if q[qs.QRY_FIELD] == 'fname':
                q_dist1 += 1
                value = values1
            elif q[qs.QRY_FIELD] == 'lname':
                q_dist2 += 1
                value = values2
            count_match = len([x for x in value if self.is_match(q, x)])
            msg = 'Query %d was: \n' \
                  'subcategory: %s\n'\
                  'field: %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'regular_expression: %s\n'\
                  'where_clause: %s\n' % (q[qs.QRY_QID], q[qs.QRY_FIELD], q[qs.QRY_SUBCAT], 
                                   q[qs.QRY_LRSS], q[qs.QRY_URSS],
                                   q[qs.QRY_SEARCHFOR], q[qs.QRY_WHERECLAUSE])
            self.assertLessEqual(count_match, q[qs.QRY_URSS]*2, msg)
            self.assertGreaterEqual(count_match, q[qs.QRY_LRSS]/2, msg)
        #check to see each field had the correct number of queries
        #ideally this number would be greater than 6 (the requested amount)
        #but because the distribution used for unit testing is so small
        #there is a greater margin of error at this scale
        self.assertGreaterEqual(q_dist1, 3, self.seed_msg)
        self.assertGreaterEqual(q_dist2, 3, self.seed_msg) 
    

    
    def testGenerateP7NotesQuery(self):
        """
        Tests wildcard query generator against a notes 'db' to make sure it is 
        generating the right queries
        """
        
        #generate a 'db' to test against
        n = [self._dist3.generate(125) for _ in xrange(1000)]
        notes = []
        for row in n:
           notes.append(str(row))

        #generate queries
        query_batches = self.P7_notes_generator.produce_query_batches()
        queries = []
        for query_batch in query_batches:
            queries += query_batch.produce_queries()
        
        #check to see right number of queries generated
        self.assertGreater(len(queries), 0, self.seed_msg)
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        for q in queries:
            self.assertEqual('P7', q[qs.QRY_CAT], self.seed_msg)
            count_match = len([x for x in notes if self.is_match(q, x)])
            msg = 'Query %d was: \n' \
                  'subcategory: %s\n'\
                  'field: %s\n'\
                  'r_lower: %d\n'\
                  'r_upper: %d\n'\
                  'regular_expression: %s\n'\
                  'where_clause: %s\n' % (q[qs.QRY_QID], q[qs.QRY_FIELD], q[qs.QRY_SUBCAT], 
                                   q[qs.QRY_LRSS], q[qs.QRY_URSS],
                                   q[qs.QRY_SEARCHFOR], q[qs.QRY_WHERECLAUSE])
            self.assertLessEqual(count_match, q[qs.QRY_URSS]*2.5, msg)
            self.assertGreaterEqual(count_match, q[qs.QRY_LRSS]/2, msg)
 
        
        
