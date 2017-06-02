# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            ATLH
#  Description:        Tests for equality_query_generator
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  6 August 2012  ATLH            Original version
# *****************************************************************

from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..', '..')
sys.path.append(base_dir)

import unittest
import time
import keyword_query_generator as kqg
import spar_python.common.spar_random as spar_random 
import spar_python.common.distributions.text_generator as text_generator
import StringIO as s
import spar_python.query_generation.query_schema as qs
import spar_python.data_generation.spar_variables as sv

class KeywordQueryGeneratorTest(unittest.TestCase):
    
    def setUp(self):
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        #set up intitialization values    
        sub_cat = 'word'
        f = s.StringIO('''Buck had accepted the rope with quiet dignity. To be sure, it 
                unwonted performance: but he had learned to trust in men he knew, and to 
                give them credit for a wisdom that outreached his own. But when the ends 
                of the ropes were placed in the strangers hands, he growled menacingly. 
                He had merely intimated his displeasure, in his pride believing that to 
                intimate was to command. But to his surprise the rope tightened around 
                his neck, shutting off his breath. In quick rage he sprang at the man, 
                who met him halfway, grappled him close by the throat, and with a deft 
                twist threw him over on his back. Then the rope tightened mercilessly, 
                while Buck struggled in a fury, his tongue lolling out of his mouth and 
                his great chest. Never in all his life had he been so 
                vilely treated, and never in all his life had he been so angry. But his 
                strength ebbed, his eyes glazed, and he knew nothing when the train was 
                flagged and the two men threw him into the baggage car.''')
        self._kw_dist = text_generator.TextGenerator((f,))
        fields = [sv.VARS.NOTES3]
        dists = [self._kw_dist]
        other_fields = ['no_queries', 'rss','keyword_len','type']
        other_cols = [[3, 60, 4, 'word'], [3, 60, 5, 'word'],
                      [3, 75, 4, 'stem'], [3, 60, 5, 'stem']]
        self.generator = kqg.KeywordQueryGenerator('P3',sub_cat, ["LL"],dists, fields, 1000,
                                                    100, other_fields, other_cols)
        
    @unittest.skip("Sporadically fails, not sure why")
    def testGenerateQuery(self):     
        """
        Tests equality query generator against a 'db' to make sure it is 
        generating the right queries
        """
        
        #generate a 'db' to test against
        notes = [self._kw_dist.generate(125) for _ in xrange(1000)]
        
        #generate queries
        query_batches = self.generator.produce_query_batches()
        queries = []
        for query_batch in query_batches:
            queries += query_batch.produce_queries()
        
        #check to see right number of queries generated

        self.assertGreaterEqual(len(queries), 6, self.seed_msg)
        
        #check queries against 'db' to make sure they match within a factor 
        #of two
        word = 0
        stem = 0
        working_queries = 0
        non_working_queries = []
        for q in queries:
            if q[qs.QRY_TYPE] == 'word':
                x = lambda generated_text: \
                        generated_text.contains_upper(q[qs.QRY_SEARCHFOR])
                word +=1
            elif q[qs.QRY_TYPE] == 'stem':
                x = lambda generated_text: \
                        generated_text.contains_stem(q[qs.QRY_SEARCHFOR])
                stem +=1
                
            count_match = len([note for note in notes if x(note)])
            msg = 'Query %d was: \n' \
                  'sub_cat: %s\n'\
                  'field: %s\n'\
                  'type: %s\n'\
                  'rss: %d\n'\
                  'value: %s\n' % (q[qs.QRY_QID], q[qs.QRY_SUBCAT], 
                                      q[qs.QRY_FIELD], q[qs.QRY_TYPE], 
                                      q[qs.QRY_RSS], q[qs.QRY_SEARCHFOR])
            if count_match <= q[qs.QRY_URSS]*4 and count_match >= q[qs.QRY_LRSS]/4:
                working_queries+=1
            else:
                non_working_queries.append(msg)
                
        fail_msg = ''
        for msg in non_working_queries[:3]:
            fail_msg += msg
        self.assertGreaterEqual(working_queries, 6, fail_msg)
        #check to see each field had the correct number of queries
        #ideally this number would be greater than 6 (the requested amount)
        #but because the distribution used for unit testing is so small
        #there is a greater margin of error at this scale
        self.assertGreaterEqual(word, 3, self.seed_msg)
        self.assertGreaterEqual(stem, 3, self.seed_msg)
