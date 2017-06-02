# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            MZ
#  Description:        Regressional analysis tool for testing SPAR
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  30 May 2013   MZ             Original Version
# *****************************************************************

import unittest
import lmregress as lmr
import numpy as np
import random
import ta1_database as t1db
import ta1_constants as t1c
import os

class lmrtest(unittest.TestCase):
    
    def setUp(self):
        self.inps = list(np.linspace(0, 10, 100))
        self.betas = (random.randint(1,12),random.randint(1,15),random.randint(1,200))
        self.outs = []
        for n in self.inps:
            self.outs.append(tempfunction(n,*betas)) + random.randint(1,7)
        #from ta1_database_test
        test_db_path = "./example%s.db"
        counter = 0
        while os.path.exists(test_db_path % str(counter)):
            counter += 1
        self.test_db_path = test_db_path % str(counter)
        self.database = ta1_results_db(self.test_db_path, None)
        self.tool = RegressionTool(database,tempfunction,'DB_SIZE',tempcheck)
    def tempfunction(x,a,b,c):
        return x*a + b^x +c

    def tempcheck(x):
        return true

    def test_construction(self): #Should pass unless something catastrophic happened

        self.assertTrue(self.tool)

    def test_accuracy(self):
        self.tool.update()
        for n in range(len(betas)):
            self.assertClose(betas[n],tool.coefficients[n],.5)

