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

class Ta1OverviewP1OtherIbmSection(t1soc.Ta1OverviewCommonSection):
    """The Equality-Or overview section of the TA1 report."""

    def __init__(self, jinja_template, report_generator):
        """Initializes the section with a jinja template and a report generator.
        """
        cat = t1s.CATEGORIES.P1
        subcat = t1s.SUBCATEGORIES[cat].otheribm
        super(Ta1OverviewP1OtherIbmSection, self).__init__(
            jinja_template, report_generator, cat, subcat)

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        self._store_common_latency_graph(
            simple_fields=[(t1s.DBP_TABLENAME, t1s.DBP_SELECTIONCOLS),
                           (t1s.DBF_TABLENAME, t1s.DBF_P1NUMCLAUSES)],
            label_template="select %s %s-clause queries")
