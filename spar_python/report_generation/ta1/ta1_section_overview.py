# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        Section class
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  19 Sep 2013   SY             Original version
# *****************************************************************

# general imports:
import logging

# SPAR imports:
import spar_python.report_generation.ta1.ta1_section as section
import spar_python.report_generation.ta1.ta1_analysis_input as t1ai
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.ta1.ta1_config as config

# LOGGER:
LOGGER = logging.getLogger(__name__)

class Ta1OverviewSection(section.Ta1Section):
    """The superclass of all of the query type specific overview sections of
    the TA1 report"""

    def __init__(self, jinja_template, report_generator):
        """Initializes the section with a jinja template, a report generator,
        and a query category."""
        super(Ta1OverviewSection, self).__init__(
            jinja_template, report_generator)
        # create the input object for this section:
        self._inp = t1ai.Input()
        # find the present databases:
        present_databases = self._report_generator.get_present_cats(
            cat=False, subcat=False, subsubcat=False, dbnr=True, dbrs=True)
        for (numrecords, recordsize) in config.MAIN_DB_HEIRARCHY:
            if (numrecords,
                recordsize) in present_databases:
                self._inp[t1s.DBF_NUMRECORDS] = numrecords
                self._inp[t1s.DBF_RECORDSIZE] = recordsize
                break
        if not (self._inp.get(t1s.DBF_NUMRECORDS)
                and self._inp.get(t1s.DBF_RECORDSIZE)):
            self._inp[t1s.DBF_NUMRECORDS] = 0
            self._inp[t1s.DBF_RECORDSIZE] = 0
            for (numrecords,
                 recordsize) in present_databases:
                if numrecords > self._inp[t1s.DBF_NUMRECORDS]:
                    self._inp[t1s.DBF_NUMRECORDS] = numrecords
                    self._inp[t1s.DBF_RECORDSIZE] = recordsize
                elif numrecords == self._inp[t1s.DBF_NUMRECORDS]:
                    if recordsize > self._inp[t1s.DBF_RECORDSIZE]:
                        self._inp[t1s.DBF_RECORDSIZE] = recordsize
            if (self._inp.get(t1s.DBF_NUMRECORDS)
                and self._inp.get(t1s.DBF_RECORDSIZE)):
                LOGGER.warning(
                    "No 'official' databases found! Using the one with "
                    "the largest number of records (%s records of size %s)." % (
                        str(self._inp[t1s.DBF_NUMRECORDS]),
                        str(self._inp[t1s.DBF_RECORDSIZE])))
            else:
                assert False, "No useable data in the results database."
        

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._outp[
            "maindb_short_name"] = self._inp.test_db.get_short_database_name()
        self._outp[
            "maindb_short_name_lower"] = self._inp.test_db.get_short_database_name(
                lower=True)
        self._outp[
            "maindb_long_name_lower"] = self._inp.test_db.get_database_name(
                lower=True)
    
