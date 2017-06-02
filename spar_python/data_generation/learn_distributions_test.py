# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            jch
#  Description:        Tests for learn_distributions
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Sep 2012   jch            Original version
# *****************************************************************
from __future__ import division
import os
import sys
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.data_generation.learn_distributions as learn_distributions 
from spar_python.common.distributions.distribution_holder import *
from spar_python.common.distributions.base_distributions import *
from spar_python.common.distributions.bespoke_distributions import *
import spar_python.data_generation.spar_variables as sv
import spar_python.common.spar_random as spar_random
import StringIO as stringio
import unittest
import logging
import tempfile
import spar_python.data_generation.learning.mock_data_files as mock_data_files
import time


                                                              
# Note: need this to make mock options
class Options(object):
    pass


class FilesGeneratorTest(unittest.TestCase):
    pass





class LearnPumsDataTest(unittest.TestCase):

    def setUp(self):
 
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)
        
        pums_data_raw = mock_data_files.mock_pums_data
        mock_file = stringio.StringIO(pums_data_raw)
        pums_files = [("mock file", mock_file)]
        
        self.log = stringio.StringIO()
        dummy_logger = logging.getLogger('dummy')
        dummy_logger.addHandler(logging.StreamHandler(self.log))
        dummy_logger.setLevel(logging.DEBUG)
        
        learner_options = Options()
        learner_options.verbose = True
 
        self.pums_dict = \
            learn_distributions.learn_pums_dists(learner_options,
                                                 dummy_logger,
                                                 pums_files)



    def ratios_close(self, ratio1, ratio2):
        self.assertGreater(ratio1, ratio2 * .5, self.seed_msg)
        self.assertLess(ratio1, ratio2 * 2, self.seed_msg)
        
        
    def get_many_samples(self, var, num_samples, ind_vars=None):
        results_dict = {}
        for i in xrange(num_samples):
            if ind_vars:
                s = self.pums_dict[var].generate(ind_vars)
            else:
                s = self.pums_dict[var].generate()

            try:
                results_dict[s] +=1
            except KeyError:
                results_dict[s] = 1
        return results_dict
        
        
        
        
    def test_keys(self):
        expected_keys = sv.PUMS_ORDER
        expected_keys.sort()
        received_keys = self.pums_dict.keys()
        received_keys.sort()
        self.assertEqual(expected_keys, received_keys, self.seed_msg)
        self.assertNotIn(None, received_keys, self.seed_msg)


        
    def test_sex(self):
                        
        genders = self.pums_dict[sv.VARS.SEX].support()
        self.assertEqual(genders, 
                         set([sv.SEX.Female,
                              sv.SEX.Male]), 
                         self.seed_msg)

        num_samples = 1000
        results_dict = self.get_many_samples(sv.VARS.SEX,
                                             num_samples)
    
        for gender in genders:
            self.ratios_close(results_dict[gender] / num_samples, 0.5)
        
        self.assertNotIn(None, genders, self.seed_msg)
        
        
    def test_citizenship(self):
        results_dict = self.get_many_samples(sv.VARS.CITIZENSHIP,
                                             1000)
        results = set(results_dict.keys())
        possibilities = set(sv.CITIZENSHIP.numbers_generator())
        self.assertSetEqual(results, possibilities, self.seed_msg)
        
        
        self.ratios_close(results_dict[sv.CITIZENSHIP.Yes_Born_In_US] \
                          / results_dict[sv.CITIZENSHIP.No], 
                          10)
        

        self.assertNotIn(None, results_dict, self.seed_msg)




    def test_age(self):
        results_dict = self.get_many_samples(sv.VARS.AGE,
                                             10000)

        self.assertGreater(results_dict[15],
                           results_dict[80], self.seed_msg)

        self.assertNotIn(None, results_dict, self.seed_msg)

        for key in results_dict:
            self.assertGreater(key, -1, self.seed_msg)
            
            # Note: this test only works because the PUMS data is
            # top-coded: ages above some threshold are rounded
            # down. If we ever fix that, this test will break. This is
            # to be expected, and the test will need revision in accordance
            # with the way we have expanded the top ages.
            self.assertLess(key, 105, self.seed_msg)

 
    def test_age_distribution(self):
        results_dict = self.get_many_samples(sv.VARS.AGE,
                                             100000)

        # Note: the following ratios are fragile and depend on our
        # mock datas
        num_1s = results_dict[1]
        num_10s = results_dict[10]
        num_35s = results_dict[35]
        num_86s = results_dict[86]
        
        self.ratios_close(num_1s / num_10s, 1)

        self.ratios_close(num_35s / num_86s, 10)
        
    
    def test_income1(self):
        '''
        Check the distribution of incomes for illegal values. Note: PUMS data
        actually lets incomes vary between -$19,998 (ie, losses) to 
        $5,000,000. (Incomes outside this range get rounded to the nearest
        boundary-value.) However, we are fuzzing incomes by a factor stored 
        in learn_distributions.INCOME_FUZZ_FACTOR
        '''
        
        ages = xrange(106)
        for age in ages:
            # Note: age must be a string
            age_str = str(age)
            results_dict = self.get_many_samples(sv.VARS.INCOME,
                                                 100,
                                                 {sv.VARS.AGE: age_str})
            
            self.assertNotIn(None, results_dict, self.seed_msg)
            fuzz_factor = learn_distributions.INCOME_FUZZ_FACTOR
            upper_bound = 5 * (10**6) * (1 + fuzz_factor)
            lower_bound = -19998 * (1 + fuzz_factor)
            
            for key in results_dict:
                key_int = int(key)
                self.assertGreaterEqual(key_int, lower_bound, self.seed_msg)
                self.assertLessEqual(key_int, upper_bound, self.seed_msg)


    def test_income2(self):
        '''
        Spot-check the distributions of incomes for a few ages against PUMS
        data. Note that the constants of this test depend crucially on the 
        specifics of the mock-pums file.
        '''
        # Note: age must be a string, and was carefully-selected to be in
        # the mock data
        age = 0
        num_rows = 10000
        results_dict = self.get_many_samples(sv.VARS.INCOME,
                                             num_rows,
                                             {sv.VARS.AGE : age})
        self.assertDictEqual(results_dict, {age: num_rows})


        age = 18
        results_dict = self.get_many_samples(sv.VARS.INCOME,
                                             num_rows,
                                             {sv.VARS.AGE : age})
        # The underlying income distribution will produce values
        # at 0, 400, and 5700. We will need to sum up all the values
        # 'close' to these values
        
        def close(val, target):
            lower_bound = target * (1 - learn_distributions.INCOME_FUZZ_FACTOR)
            upper_bound = target * (1 + learn_distributions.INCOME_FUZZ_FACTOR)
            return (val >= lower_bound) and (val <= upper_bound)
        
        num_0 = 0
        num_400 = 0
        num_5700 = 0
        
        for val in xrange(7000):
            if close(val, 0):
                num_0 += results_dict.get(val, 0)
            if close(val, 400):
                num_400 += results_dict.get(val, 0)
            if close(val, 5700):
                num_5700 += results_dict.get(val, 0)
        
        self.ratios_close(num_0 / num_400, 4)
        self.ratios_close(num_0 / num_5700, 2)


    def test_race(self):
        ind_vars = {sv.VARS.CITIZENSHIP: sv.CITIZENSHIP.Yes_Born_In_US}
        results_dict = self.get_many_samples(sv.VARS.RACE,
                                             10000,
                                             ind_vars)
        results = set(results_dict.keys())
        possibilities = set(sv.RACE.numbers_generator())
        self.assertSetEqual(results, possibilities, self.seed_msg)
        
        self.assertNotIn(None, results_dict, self.seed_msg)
        

    def test_race2(self):
        '''
        Spot-check the race distribution for a few citizenships.
        Note that the constants of this test depend entirely on the specifics 
        of our mock-pums file.
        '''
        ind_vars = {sv.VARS.CITIZENSHIP: 
                    sv.CITIZENSHIP.Yes_Born_In_US_Territory}
        results_dict = self.get_many_samples(sv.VARS.RACE,
                                             10000,
                                             ind_vars)
        num_asian = results_dict[sv.RACE.Asian]
        num_white = results_dict[sv.RACE.White]
        self.ratios_close(num_white / num_asian, 2)


        ind_vars = {sv.VARS.CITIZENSHIP: sv.CITIZENSHIP.Yes_Born_In_US}
        results_dict = self.get_many_samples(sv.VARS.RACE,
                                             10000,
                                             ind_vars)
        num_american_indian = results_dict[sv.RACE.American_Indian]
        num_white = results_dict[sv.RACE.White]
        self.ratios_close(num_white / num_american_indian, 100)


    def test_state(self):
        ind_vars = {sv.VARS.RACE: None}
        results_dict = self.get_many_samples(sv.VARS.STATE,
                                             50000,
                                             ind_vars)
        results = set(results_dict.keys())
        possibilities = set(sv.STATES.numbers_generator())
        self.assertSetEqual(results, possibilities, self.seed_msg)
        
        self.assertNotIn(None, results_dict, self.seed_msg)


    def test_state2(self):
        '''
        Spot-check the state distribution for a few citizenships.
        Note that the constants of this test depend entirely on the specifics 
        of our mock-pums file.
        '''
        num_rows = 10000
        ind_vars = {sv.VARS.RACE: sv.RACE.Alaska_Native}
        results_dict = self.get_many_samples(sv.VARS.STATE,
                                             num_rows,
                                             ind_vars)
        self.assertDictEqual(results_dict, {sv.STATES.Alaska : num_rows})
        
        
        ind_vars = {sv.VARS.RACE: sv.RACE.African_American}
        results_dict = self.get_many_samples(sv.VARS.STATE,
                                             num_rows,
                                             ind_vars)

        num_california = results_dict[sv.STATES.California]
        num_arkansas = results_dict[sv.STATES.Arkansas]
        self.ratios_close(num_california / num_arkansas, 10)

        

    def test_weeks_worked(self):
        ind_vars = {sv.VARS.AGE: None}
        results_dict = self.get_many_samples(sv.VARS.WEEKS_WORKED,
                                             1000,
                                             ind_vars)
        self.assertNotIn(None, results_dict, self.seed_msg)

        for k in results_dict:
            weeks = int(k)
            self.assertGreaterEqual(weeks, 0, self.seed_msg)
            self.assertLess(weeks, 53, self.seed_msg)


    def test_weeks_worked2(self):
        '''
        Spot-check the weeks-worked distribution for a few ages.
        Note that the constants of this test depend entirely on the specifics 
        of our mock-pums file.
        '''
        num_rows = 10000
        ind_vars = {sv.VARS.AGE: 0}
        results_dict = self.get_many_samples(sv.VARS.WEEKS_WORKED,
                                             num_rows,
                                             ind_vars)
        self.assertDictEqual(results_dict, {0: num_rows})

        ind_vars = {sv.VARS.AGE: 16}
        results_dict = self.get_many_samples(sv.VARS.WEEKS_WORKED,
                                             num_rows,
                                             ind_vars)
        num_0 = results_dict[0]
        num_36 = results_dict[36]
        
        self.ratios_close(num_0 / num_36, 6)


    def test_hours_worked(self):
        ind_vars = {sv.VARS.WEEKS_WORKED: None}
        results_dict = self.get_many_samples(sv.VARS.HOURS_WORKED,
                                             10000,
                                             ind_vars)
        self.assertNotIn(None, results_dict, self.seed_msg)

        for k in results_dict:
            hours = int(k)
            self.assertGreaterEqual(hours, 0, self.seed_msg)
            self.assertLess(hours, 24 * 7, self.seed_msg)
        

    def test_hours_worked2(self):
        '''
        Spot-check the hours-worked distribution for a few values of weeks-
        worked. Note that the constants of this test depend entirely on the
        specifics of our mock-pums file.
        '''
        num_rows = 10000
        ind_vars = {sv.VARS.WEEKS_WORKED: 0}
        results_dict = self.get_many_samples(sv.VARS.HOURS_WORKED,
                                             num_rows,
                                             ind_vars)
        self.assertDictEqual(results_dict, {0: num_rows})

        ind_vars = {sv.VARS.WEEKS_WORKED: 52}
        results_dict = self.get_many_samples(sv.VARS.HOURS_WORKED,
                                             num_rows,
                                             ind_vars)
        num_40 = results_dict[40]
        num_50 = results_dict[50]
        
        self.ratios_close(num_40 / num_50,  1281/395)





    def test_military_service(self):
        ind_vars = {sv.VARS.AGE: None,
                    sv.VARS.SEX: sv.SEX.Male}
        results_dict = self.get_many_samples(sv.VARS.MILITARY_SERVICE,
                                             10000,
                                             ind_vars)
        results = set(results_dict.keys())
        possibilities = set(sv.MILITARY_SERVICE.numbers_generator())
        self.assertSetEqual(results, possibilities, self.seed_msg)
        
        self.assertNotIn(None, results_dict, self.seed_msg)


    def test_military_service2(self):
        '''
        Spot-check the military-server distribution for a few age/sex pairs. 
        Note that the constants of this test depend entirely on the
        specifics of our mock-pums file.
        '''
        num_rows = 10000
        ind_vars = {sv.VARS.AGE: 0, sv.VARS.SEX: sv.SEX.Male}
        results_dict = self.get_many_samples(sv.VARS.MILITARY_SERVICE,
                                             num_rows,
                                             ind_vars)
        self.assertDictEqual(results_dict, 
                             {sv.MILITARY_SERVICE.Under_17: num_rows})

        ind_vars = {sv.VARS.AGE: 55, sv.VARS.SEX: sv.SEX.Female}
        results_dict = self.get_many_samples(sv.VARS.MILITARY_SERVICE,
                                             num_rows,
                                             ind_vars)
        ratio = results_dict[sv.MILITARY_SERVICE.Never_Active_Duty] \
            / results_dict[sv.MILITARY_SERVICE.Training]
        self.ratios_close(ratio, 4)




    def test_marital_status(self):
        ind_vars = {sv.VARS.MILITARY_SERVICE : None}
        results_dict = self.get_many_samples(sv.VARS.MARITAL_STATUS,
                                             1000,
                                             ind_vars)
        results = set(results_dict.keys())
        possibilities = set(sv.MARITAL_STATUS.numbers_generator())
        self.assertSetEqual(results, possibilities, self.seed_msg)
        
        self.assertNotIn(None, results_dict, self.seed_msg)

    def test_marital_status2(self):
        '''
        Spot-check the marital_status distribution for a few military-
        service/age pairs. Note that the constants of this test depend entirely
        on the specifics of our mock-pums file.
        '''
        num_rows = 10000
        ind_vars = {sv.VARS.AGE: 5, 
                    sv.VARS.MILITARY_SERVICE: sv.MILITARY_SERVICE.Under_17}
        results_dict = self.get_many_samples(sv.VARS.MARITAL_STATUS,
                                             num_rows,
                                             ind_vars)
        self.assertDictEqual(results_dict, 
                             {sv.MARITAL_STATUS.Never_Married: num_rows})


        ind_vars = {sv.VARS.AGE: '27', 
                    sv.VARS.MILITARY_SERVICE : 
                        sv.MILITARY_SERVICE.Previous_Active_Duty}
        results_dict = self.get_many_samples(sv.VARS.MARITAL_STATUS,
                                             num_rows,
                                             ind_vars)
        ratio = results_dict[sv.MARITAL_STATUS.Married] \
            / results_dict[sv.MARITAL_STATUS.Never_Married]
        self.ratios_close(ratio, 21/9)


    def test_grade_enrolled(self):
        ind_vars = {sv.VARS.MILITARY_SERVICE : None,
                    sv.VARS.AGE: None}
        results_dict = self.get_many_samples(sv.VARS.GRADE_ENROLLED,
                                             2000,
                                             ind_vars)
        results = set(results_dict.keys())
        possibilities = set(sv.GRADE_ENROLLED.numbers_generator())
        self.assertSetEqual(results, possibilities, self.seed_msg)
        
        self.assertNotIn(None, results_dict, self.seed_msg)

    def test_grade_enrolled2(self):
        '''
        Spot-check the grade_enrolled distribution for a few military-
        service/age pairs. Note that the constants of this test depend entirely
        on the specifics of our mock-pums file.
        '''
        num_rows = 10000
        ind_vars = {sv.VARS.AGE: 3, 
                    sv.VARS.MILITARY_SERVICE: sv.MILITARY_SERVICE.Under_17}
        results_dict = self.get_many_samples(sv.VARS.GRADE_ENROLLED,
                                             num_rows,
                                             ind_vars)
        self.assertDictEqual(results_dict, 
                             {sv.GRADE_ENROLLED.Not_In_School: num_rows})


        ind_vars = {sv.VARS.AGE: 23, 
                    sv.VARS.MILITARY_SERVICE: 
                    sv.MILITARY_SERVICE.Never_Active_Duty}
        results_dict = self.get_many_samples(sv.VARS.GRADE_ENROLLED,
                                             num_rows,
                                             ind_vars)
        ratio = results_dict[sv.GRADE_ENROLLED.Not_In_School] \
            / results_dict[sv.GRADE_ENROLLED.College_undergraduate]
        self.ratios_close(ratio, 24/11)


    def test_language(self):
        ind_vars = {sv.VARS.CITIZENSHIP : None,
                    sv.VARS.RACE: None}
        results_dict = self.get_many_samples(sv.VARS.LANGUAGE,
                                             1000,
                                             ind_vars)
        results = set(results_dict.keys())
        possibilities = set(sv.LANGUAGE.numbers_generator())
        
        # Note: this tests that results is a subset of possibilities
        self.assertLessEqual(results, possibilities, self.seed_msg)
        
        self.assertNotIn(None, results_dict, self.seed_msg)
        
        self.assertGreaterEqual(len(results), 3, self.seed_msg)
        
        self.assertIn(sv.LANGUAGE.ENGLISH,
                      results_dict, 
                      self.seed_msg)

        for lang in results_dict:
            self.assertGreaterEqual(results_dict[sv.LANGUAGE.ENGLISH],
                                    results_dict[lang],
                                    self.seed_msg)


    def test_language2(self):
        '''
        Spot-check the language distribution for a few citizenship/race 
        pairs. Note that the constants of this test depend entirely
        on the specifics of our mock-pums file.
        '''
        num_rows = 10000
        ind_vars = {sv.VARS.CITIZENSHIP: sv.CITIZENSHIP.Yes_Born_In_US, 
                    sv.VARS.RACE : sv.RACE.American_Indian}
        results_dict = self.get_many_samples(sv.VARS.LANGUAGE,
                                             num_rows,
                                             ind_vars)
        self.assertDictEqual(results_dict, {sv.LANGUAGE.ENGLISH: num_rows})


        ind_vars = {sv.VARS.CITIZENSHIP: sv.CITIZENSHIP.Yes_Naturalized, 
                    sv.VARS.RACE : sv.RACE.White}
        results_dict = self.get_many_samples(sv.VARS.LANGUAGE,
                                             num_rows,
                                             ind_vars)
        ratio = results_dict[sv.LANGUAGE.SPANISH] / \
            results_dict[sv.LANGUAGE.NOT_SPECIFIED]
        self.ratios_close(ratio, 105/32)
        

class LearnNamesDataTest(unittest.TestCase):



    def setUp(self):

        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

        names_files = \
            [('male_first_names.txt', 
              stringio.StringIO(mock_data_files.mock_male_first_names)),
             ('female_first_names.txt', 
              stringio.StringIO(mock_data_files.mock_female_first_names)),
             ('last_names.txt', 
              stringio.StringIO(mock_data_files.mock_last_names))]
        
        
        self.log = stringio.StringIO()
        dummy_logger = logging.getLogger('dummy')
        dummy_logger.addHandler(logging.StreamHandler(self.log))
        dummy_logger.setLevel(logging.DEBUG)
        
        learner_options = Options()
        learner_options.verbose = True
        

        self.names_dict = \
            learn_distributions.learn_name_dists(learner_options,
                                                 dummy_logger,
                                                 names_files)
 
        (_, manipulator) = sv.PUMS_VARS_DICT[sv.VARS.SEX ]
        self.male_ind_var = {sv.VARS.SEX :
                             manipulator.to_string(sv.SEX.Male) }
        self.female_ind_var =  {sv.VARS.SEX :
                                manipulator.to_string(sv.SEX.Female)}

    



    def get_many_samples(self, generator, num_samples, arg=None):
        results_dict = {}
        for i in xrange(num_samples):
            s = generator(arg)
            try:
                results_dict[s] +=1
            except KeyError:
                results_dict[s] = 1
        return results_dict
        
                
        
    def test_keys(self):
        expected_keys = [sv.VARS.LAST_NAME, sv.VARS.FIRST_NAME]
        expected_keys.sort()
        received_keys = self.names_dict.keys()
        received_keys.sort()
        self.assertEqual(expected_keys, received_keys, self.seed_msg)


    def test_all_generate(self):
        for i in xrange(1000):
            self.names_dict[sv.VARS.LAST_NAME].generate()
            self.names_dict[sv.VARS.FIRST_NAME].generate(self.male_ind_var)
            self.names_dict[sv.VARS.FIRST_NAME].generate(self.female_ind_var)
            
        

    def test_last_names(self):
        last_name_dist = self.names_dict[sv.VARS.LAST_NAME]
        self.assertTrue(last_name_dist.support(), self.seed_msg)
        num_samples = 1000

        generator = last_name_dist.generate
        results_dict = self.get_many_samples(generator,
                                             num_samples)

        self.assertGreater(results_dict['JONES'], 
                           num_samples / 20, 
                           self.seed_msg)
        
        if 'ABAJA' in results_dict: 
            self.assertLess(results_dict['ABAJA'], 
                            num_samples / 20,
                            self.seed_msg)
        
        
    def test_male_first_names(self):
        first_name_dist = self.names_dict[sv.VARS.FIRST_NAME]

        num_samples = 1000

        generator = first_name_dist.generate
        results_dict = self.get_many_samples(generator,
                                             num_samples,
                                             self.male_ind_var)
        self.assertGreater(results_dict['JAMES'], 
                           num_samples / 20,
                           self.seed_msg)
        
        if 'ALONSO' in results_dict: 
            self.assertLess(results_dict['ALONSO'], 
                            num_samples / 100,
                            self.seed_msg)

    def test_female_first_names(self):
        first_name_dist = self.names_dict[sv.VARS.FIRST_NAME]

        num_samples = 1000

        generator = first_name_dist.generate
        results_dict = self.get_many_samples(generator,
                                             num_samples,
                                             self.female_ind_var)

        self.assertGreater(results_dict['MARY'], 
                           num_samples / 20,
                           self.seed_msg)
        
        if 'ALLYN' in results_dict: 
            self.assertLess(results_dict['ALLYN'], 
                            num_samples / 100,
                            self.seed_msg)



class LearnZipcodeTest(unittest.TestCase):



    def setUp(self):
                
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

        zipcode_files = \
            [('mock_zipcodes', 
              stringio.StringIO(mock_data_files.mock_zipcodes))]
        
        
        self.log = stringio.StringIO()
        dummy_logger = logging.getLogger('dummy')
        dummy_logger.addHandler(logging.StreamHandler(self.log))
        dummy_logger.setLevel(logging.DEBUG)
        
        learner_options = Options()
        learner_options.verbose = True
        
        self.zipcode_dict = \
            learn_distributions.learn_zipcode_dists(learner_options,
                                                    dummy_logger,
                                                    zipcode_files)
 
                
        
    def test_keys(self):
        expected_keys = set([sv.VARS.ZIP_CODE, sv.VARS.CITY])
        received_keys = set(self.zipcode_dict.keys())
        self.assertSetEqual(expected_keys, received_keys, self.seed_msg)


    def test_all_generate(self):
        zipcode_dist = self.zipcode_dict[sv.VARS.ZIP_CODE]
        city_dist = self.zipcode_dict[sv.VARS.CITY]

        num_samples = 1000

        for i in xrange(num_samples):
            for state in sv.STATES.values_generator():

                state_ind_var = {sv.VARS.STATE:
                                 state}
                zip = zipcode_dist.generate(state_ind_var)
                
                zip_ind_var = {sv.VARS.ZIP_CODE: zip}
                city = city_dist.generate(zip_ind_var)
        

    def test_specific_values_maine(self):
        zipcode_dist = self.zipcode_dict[sv.VARS.ZIP_CODE]
        city_dist = self.zipcode_dict[sv.VARS.CITY]

        state = 'Maine'
                                 
        state_ind_var = {sv.VARS.STATE: state}
        zip = zipcode_dist.generate(state_ind_var)
                    
        zip_ind_var = {sv.VARS.ZIP_CODE: zip}
        city = city_dist.generate(zip_ind_var)
        
        self.assertEqual(zip, '04660', self.seed_msg)
        self.assertEqual(city, 'Mount Desert', self.seed_msg)

    def test_specific_values_utah(self):
        zipcode_dist = self.zipcode_dict[sv.VARS.ZIP_CODE]
        city_dist = self.zipcode_dict[sv.VARS.CITY]

        state = 'Utah'
        for i in xrange(100):
            state_ind_var = {sv.VARS.STATE: state}
            zip = zipcode_dist.generate(state_ind_var)
                        
            zip_ind_var = {sv.VARS.ZIP_CODE: zip}
            city = city_dist.generate(zip_ind_var)
            
            self.assertIn(zip, ['846XX', '84001'], self.seed_msg)
            if zip == '846XX':
                self.assertEqual(city, "", self.seed_msg)
            else:
                self.assertEqual(city, 'Altamont', self.seed_msg)



class MakeDistributionHolderTest(unittest.TestCase):


    def setUp(self):
                        
        self.seed = int(time.time())
        self.seed_msg = "Random seed used for this test: %s" % self.seed
        self.longMessage = True
        spar_random.seed(self.seed)

        learner_options = Options()
        learner_options.verbose = False

        dummy_logger = logging.getLogger('dummy')
        dummy_logger.addHandler(logging.NullHandler())

        pums_files = \
            [("mock pums", 
              stringio.StringIO(mock_data_files.mock_pums_data))]
        pums_dict = \
            learn_distributions.learn_pums_dists(learner_options,
                                                 dummy_logger,
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
                                                 dummy_logger,
                                                 names_files)

        zipcode_files = \
            [('mock_zipcodes', 
              stringio.StringIO(mock_data_files.mock_zipcodes))]
        zipcode_dict = \
            learn_distributions.learn_zipcode_dists(learner_options,
                                                    dummy_logger,
                                                    zipcode_files)
        
        text_files = \
            [('mock_text', 
              stringio.StringIO(mock_data_files.mock_text_files))]
        text_engine = \
            learn_distributions.train_text_engine(learner_options, 
                                                  dummy_logger, 
                                                  text_files)

        streets_files = \
            [('mock street file', 
              stringio.StringIO(mock_data_files.mock_street_names))]
        address_dict = \
                learn_distributions.learn_street_address_dists(learner_options, 
                                                               dummy_logger, 
                                                               streets_files)

   
        
        self.dist_holder = \
            learn_distributions.make_distribution_holder(learner_options,
                                                         dummy_logger,
                                                         pums_dict,
                                                         names_dict,
                                                         zipcode_dict,
                                                         address_dict,
                                                         text_engine)




    #
    # Other tests
    #


    def generate_all(self):
        '''
        Does the distribution-holder have a valid distribution for every
        variable it claims to provide?
        '''
        # Note: mimics code from data_generator_engine.generate_row_dict
        row_dict = {}
        var_order = self.dist_holder.var_order
        dist_dict = self.dist_holder.dist_dict
        for var in var_order:
            dist = dist_dict[var]
            v = dist.generate(row_dict)
            self.assertIsNotNone(v, self.seed_msg)
 
