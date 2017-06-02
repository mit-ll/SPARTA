# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for pums_record.py 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  09 Dec 2011   omd            Original Version
# *****************************************************************

import unittest
from spar_python.data_generation.learning.pums_record_handler \
    import PUMSRecordHandler
from StringIO import StringIO
from spar_python.common.enum import Enum
import spar_python.data_generation.learning.pums_variables as pums_variables
import os.path
import spar_python.data_generation.spar_variables as sv
import spar_python.common.contingency_table as ct
import collections

class PUMSRecordHandlerTest(unittest.TestCase):
    def test_short(self):
        """Test that it can correctly handle just a few lines of data.
        Specifically we pull out 7 lines of data for two households and parse
        out the state and sex of the individuals and then make sure we've parsed
        things correctly by comparing to a manual parsing of the same data."""
        # This is a cut and paste of a few lines of PUMS data. It should contain
        # two households and 5 people.
        data = StringIO(
            'H000117755648004005610099979997999799977070   181'
            '20630826   18023212911  253335953638  25148887214'
            '36700180300000100207010602010101030102010 0060010'
            '80010580100011    0 01000470030     0200612003301'
            '00000100 0     0100000300000441006790120000000022'
            '141020007030000070300\n'
            'P000117701000019010000104800201100000101470101001'
            '0001102109990110625010008010000003005600040056100'
            '7070999799979997999720202020201012000002000001000'
            '0020081000560004005610070709997999799979997010101'
            '290010000000109590928Z    500043-1011501052050004'
            '0000100000000000000000000000000000000000000000000'
            '00004000010040000501\n'
            'P000117702000015020004204800201100000101470101003'
            '0701402109990110625020031010000003005600040056100'
            '7070999799979997999710202020201012000004000000000'
            '0000001000560004005610070709997999799979997010100'
            '97001500000010538045211   476041-2031101036120000'
            '3900100000000000000000000000000000000000000000000'
            '00000390010003900501\n'
            'P000117703000023030004202300201100000101470506001'
            '00013021099901200000 0031010000003005600040056100'
            '7070999799979997999710202020202012000004000000000'
            '0000001000560004005610070709997999799979997010100'
            '4300150000001078606111    231025-2020301038140002'
            '6400100000000000000000000000000000000000000000000'
            '00002640010026400501\n'
            'H000127055648003005610099999999999799979070   917'
            '31950606   91464209759  253335953638  25148887214'
            '3730011040000010020502080401010106020102000120000'
            '00100900004000    0 01000600130     0101811004001'
            '00000130 0     0100020402020220008080360000000021'
            '131010002700000027000\n'
            'P000127001000015010000103400101100000101470101001'
            '00014003299901200000 0031010000003005600030056100'
            '9070999999979999999720202020202022000004000000000'
            '0000001000560002005610070709997999799979997010100'
            '43004000000010947092MP    161119-1020401052065003'
            '1200100000000000000000000000000000000000000000000'
            '00003120010031200161\n'
            'P000127002000011020002203400101100000101470101001'
            '00013002699901200000 0056010000003005600030056100'
            '9070999999979999999720202020202022000004000000000'
            '0000001000560003005610090709999999799999997110000'
            '000000000000108560711     260027-1010601052040000'
            '00000-0420010000000000000000000000000000000000000'
            '00-0042001-004200161\n')
        # The weights we expect for the 5 people in the data
        expected_weights = (19, 15, 23, 15, 11)
        expected_states = ('Wyoming', 'Wyoming', 'Wyoming', 'Wyoming',
                'Wyoming')
        expected_sexes = ('Male', 'Female', 'Female', 'Male', 'Female')

        # Set up for the PUMSRecordHandler.
        VARIABLES = Enum('STATE', 'SEX')
        vars_dict = {VARIABLES.STATE: (sv.STATE_PARSER,
                                       sv.STATE_MANIPULATOR),
                     VARIABLES.SEX: (sv.SEX_PARSER,
                                     sv.SEX_MANIPULATOR)}
        record_handler = PUMSRecordHandler(vars_dict)
        num_people = 0
        for i, (weight, record) in \
                enumerate(record_handler.record_generator(data)):
            num_people += 1
            self.assertEqual(weight, expected_weights[i])
            self.assertEqual(record_handler.as_string(record, VARIABLES.STATE),
                    expected_states[i])
            self.assertEqual(record_handler.as_string(record, VARIABLES.SEX),
                    expected_sexes[i])

        self.assertEqual(num_people, 5)

    def test_language(self):
        """Language is pretty strange so we have special tests for it. Here I've
        cut and pasted 3 lines of PUMS data that contain the 3 special cases for
        languge: the person speaks english, the person speaks a non-english
        language, the person is under age 5 and their language is thus "not in
        universe"."""
        data = StringIO(
                'P000117701000019010000104800201100000101470101001000110210999'
                '0110625010008010000003005600040056100707099979997999799972020'
                '2020201012000002000001000002008100056000400561007070999799979'
                '9979997010101290010000000109590928Z    500043-101150105205000'
                '4000010000000000000000000000000000000000000000000000004000010'
                '040000501\n'
                'P000127001000015010000103400101100000101470101001000140032999'
                '01200000 0031010000003005600030056100907099999997999999972020'
                '2020202022000004000000000000000100056000200561007070999799979'
                '997999701010043004000000010947092MP    161119-102040105206500'
                '3120010000000000000000000000000000000000000000000000003120010'
                '031200161\n'
                'P000718903000022030110100400101100000101470500003010020050999'
                '01 00000 005601000000000000000000000000000000000000000000 0 0'
                '0 0 0 0000000000000000000000000050000000000000000000000000000'
                '00000000000000000000000000000000000000000000-00000000000000  '
                '0      0      0     0     0     0      0      0       0      '
                '501\n')

        expected_weights = (19, 15, 22)
        expected_langs = (sv.LANGUAGE.SPANISH, sv.LANGUAGE.ENGLISH,
                sv.LANGUAGE.NOT_IN_UNIVERSE)
        VARIABLES = Enum('LANGUAGE')
        vars_dict = {VARIABLES.LANGUAGE: (sv.LANGUAGE_PARSER,
                                          sv.LANGUAGE_MANIPULATOR)}

        record_handler = PUMSRecordHandler(vars_dict)
        num_found = 0
        for i, (weight, record) in \
                enumerate(record_handler.record_generator(data)):
           num_found += 1
           self.assertEqual(weight, expected_weights[i])
           self.assertEqual(record[VARIABLES.LANGUAGE], expected_langs[i])

        self.assertEqual(num_found, len(expected_weights))


    def test_wyoming(self):
        """This is a big test to make sure we're really getting
        everyting right.  We parse the entire file for the state of
        Wyoming and then compare the numbers to other data sources to
        check for accuracy.

        Wyoming was picked because it's the least populated state and
        thus the test runs the fastest.

        Note that doing this test relies on the availability of the
        Wyoming data and that's too big to check into svn. It can be
        retreived by running get_data.sh in this directory. If that
        data is missing this prints a warning and exits. That way our
        unit tests don't fail if people haven't downloaded the data."""
        this_dir = os.path.dirname(__file__)
        wyoming_path = os.path.join(this_dir, 'data/PUMS',
                'REVISEDPUMS5_56.TXT')
        if not os.path.exists(wyoming_path):
            print ('WARNING: Not running full record test as the data files '
                   'have not been downloaded.')
            return

        
        wyoming_file = file(wyoming_path, 'r')
        VARIABLES = Enum('STATE', 'SEX', 'EDUCATION', 'AGE')
        vars_dict = {VARIABLES.STATE: (sv.STATE_PARSER,
                                       sv.STATE_MANIPULATOR),
                     VARIABLES.SEX: (sv.SEX_PARSER,
                                     sv.SEX_MANIPULATOR),
                     VARIABLES.EDUCATION:
                        (sv.EDUCATION_PARSER,
                         sv.EDUCATION_MANIPULATOR),
                     VARIABLES.AGE: (sv.AGE_PARSER,
                                     sv.AGE_MANIPULATOR),
                     }
        record_handler = PUMSRecordHandler(vars_dict)
        
        # compute total number of records, total weighted number of records,
        # total # of males and females, and the number of people >= age 25 who
        # graduated high school and who graduated from college
        sex_totals = {sv.SEX.Male: 0, sv.SEX.Female: 0}
        unweighted_count = 0
        weighted_count = 0
        high_school_count = 0
        college_count = 0
        num_ge_25 = 0
        for weight, record in record_handler.record_generator(wyoming_file):
            unweighted_count += 1
            weighted_count += weight
            sex_totals[record[VARIABLES.SEX]] += weight
            if record[VARIABLES.AGE] >= 25:
                num_ge_25 += 1
                if record[VARIABLES.EDUCATION] >= \
                        sv.EDUCATION.High_school_graduate:
                    high_school_count += 1
                if record[VARIABLES.EDUCATION] >= \
                        sv.EDUCATION.Bachelors_degree:
                    college_count += 1
                

        # These two numbers are published in the PUMS 5% sample documentation
        # as a correctness check so they should match exactly.
        # self.assertEqual(unweighted_count, 25142)
        # The PUMS data actually publishes the number of unweighted records
        # *including those with 0 weight*. As those make no sense we skip them
        # so we end up with fewer records than the docs indicate we should
        # have.
        self.assertEqual(unweighted_count, 25125)
        self.assertEqual(weighted_count, 493849)

        # There does not appear to be any published data on the number of males
        # and females by state in the PUMS data. Naturally it should closely
        # match the published numbers that come from the 100% data but it won't
        # be exact (indeed Appendix I of the PUMS documentatin gives the total
        # populaton of Wyoming as the total population of Wyoming in the PUMS
        # data as 493849 while the true number as published in Profile of
        # General Demographic Characteristics document is given as 493782). Thus
        # we can't expect an exact match but the ratio of Male to Female should
        # roughly matched the published figures.
        fraction_male_pums = (float(sex_totals[sv.SEX.Male]) /
                float(sex_totals[sv.SEX.Male] +
                    sex_totals[sv.SEX.Female]))
        fraction_male_published = float(248374) / float(248374 + 245408)
        # Less than 3% error
        self.assertLess(abs(fraction_male_pums - fraction_male_published), 0.03)

        # Similar to the above we compute fraction of people >= 25 with various
        # levels of education and compare to published data
        fraction_high_school = float(high_school_count) / float(num_ge_25)
        self.assertLess(abs(fraction_high_school - 0.879), 0.03)

        fraction_college = float(college_count) / float(num_ge_25)
        self.assertLess(abs(fraction_college - 0.219), 0.03)

    def assertClose(self, actual, expected, allowed_diff):
        self.assertLess(abs(actual - expected), allowed_diff,
                msg = '%s is not within %s of expected value %s' %
                (actual, allowed_diff, expected))

    # TODO(odain) This should really be broken up into a lot of separate tests -
    # one test per variabe we're checking. To make that efficient we should have
    # a static initializer read the data and populate the contingency table and
    # then have each test use the existing data.
    def test_spar_vars_wyoming(self):
        """Like test_wyoming but we build a contingency table of all the current
        spar variables defined in spar_variables. This lets us test to make sure
        a bunch of stuff is correctly parsed."""
        this_dir = os.path.dirname(__file__)
        wyoming_path = os.path.join(this_dir, 'data/PUMS',
                'REVISEDPUMS5_56.TXT')
        if not os.path.exists(wyoming_path):
            print ('WARNING: Not running full record test as the data files '
                   'have not been downloaded.')
            return

         
        wyoming_file = file(wyoming_path, 'r')
        record_handler = PUMSRecordHandler(sv.PUMS_VARS_DICT)

        
        income_table = collections.Counter()
        citizen_table = collections.Counter()
        lang_table = collections.Counter()
        hrs_age_table = collections.Counter()
        weeks_age_table = collections.Counter()
        
        for (weight, record) in record_handler.record_generator(wyoming_file):
            income_table[record[sv.VARS.INCOME]] += weight
            citizen_table[record[sv.VARS.CITIZENSHIP]] += weight
            lang_table[record[sv.VARS.LANGUAGE]] += weight
            hrs_age_table[(record[sv.VARS.AGE],
                           record[sv.VARS.HOURS_WORKED])] += weight
            weeks_age_table[(record[sv.VARS.AGE],
                             record[sv.VARS.WEEKS_WORKED])] += weight



        # Compare # of people with various incomes to the data published by
        # Social Explorer (socialexplorer.com)
        total_income_in_range = \
            sum((income_table[x] for x in xrange(25000, 35000)))
        self.assertClose(total_income_in_range, 50632, 1000)
        total_income_in_range = \
            sum((income_table[x] for x in xrange(75000, 100000)))
        self.assertClose(total_income_in_range, 7293, 1000)

        # Compared to published numbers. The agreement isn't great hence the
        # high tolerances on the assertClose calls but too close to be
        # coincidence so I think we're parsing it right and this is just due to
        # issues with the PUMS data.
        self.assertClose(citizen_table[sv.CITIZENSHIP.Yes_Naturalized],
                5121, 1000)
        self.assertClose(citizen_table[sv.CITIZENSHIP.No], 6084, 1000)
        self.assertClose(citizen_table[sv.CITIZENSHIP.Yes_Born_In_US],
                478776, 10000)

        # Compare language stats to published numbers from Social Explorer
        self.assertClose(lang_table[sv.LANGUAGE.SPANISH], 18606, 1000)
        self.assertClose(lang_table[sv.LANGUAGE.GERMAN], 2382, 500)
        self.assertClose(lang_table[sv.LANGUAGE.ENGLISH], 433324, 2000)

        # Make sure hours worked and weeks worked are always NULL for
        # individuals under 16.
        for age, h_worked in hrs_age_table.keys():
            if age < 16:
                self.assertEqual(h_worked, 0)
        # Make sure the values aren't all None for older workers - there should
        # definitely be more than 100 workers aged 40 working 40 hours/week.
        self.assertGreater(hrs_age_table[(40, 40)], 100)

        # Basically the same test as above but for weeks worked last year.
        for age, w_worked in weeks_age_table:
            if age < 16:
                self.assertEqual(w_worked, 0)
        self.assertGreater(weeks_age_table[(40, 50)], 100)
