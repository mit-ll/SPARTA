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
import spar_python.report_generation.ta1.ta1_section_overview_common as t1soc
import spar_python.report_generation.ta1.ta1_schema as t1s

# LOGGER:
LOGGER = logging.getLogger(__name__)

class Ta1OverviewP8P9OtherSection(t1soc.Ta1OverviewCommonSection):
    """The P8 / P9 other overview section of the TA1 report."""

    def __init__(self, jinja_template, report_generator, cat):
        """Initializes the section with a jinja template and a report generator.
        """
        subcat = t1s.SUBCATEGORIES[cat].other
        super(Ta1OverviewP8P9OtherSection, self).__init__(
            jinja_template, report_generator, cat, subcat)
        
    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        correctness_getter = self._report_generator.get_correctness_getter(
            cat=self._inp["cat_number"], subcat=self._inp["subcat_number"])
        if correctness_getter.get_num_correct > 0:
            self._outp["success"] = True
        else:
            self._outp["success"] = False
