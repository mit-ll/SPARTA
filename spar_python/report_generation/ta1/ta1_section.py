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
import os

# SPAR imports:
import spar_python.report_generation.ta1.ta1_schema as t1s
import spar_python.report_generation.common.section as section
import spar_python.report_generation.ta1.ta1_analysis_input as t1ai

class Ta1Section(section.Section):
    """A report section.
    This is the superclass for the section classes, which are responsible for
    creating LaTeX code for each section of the report.
    """

    def __init__(self, jinja_template, report_generator):
        super(Ta1Section, self).__init__(jinja_template, report_generator)
        # TODO: make outp a dict here
        self._outp = {} # all section-specific information for the template will
                        # be stored here

    def get_tag(self, inp=None, aux=None):
        """Returns the tag for the LaTeX object.
        Attributes are listed in the tag in a canonical order.

        Args:
            inp: an Input object
            aux: any auxiliary string
        """
        if not inp: inp = t1ai.Input()
        tag =  "_".join([str(arg).replace(" ", "") for arg in [
            type(self).__name__,
            self._config.performername,
            inp.get(t1s.DBF_NUMRECORDS),
            inp.get(t1s.DBF_RECORDSIZE),
            inp.get(t1s.DBF_CAT),
            inp.get(t1s.DBF_SUBCAT),
            inp.get(t1s.DBF_SUBSUBCAT),
            inp.get(t1s.DBA_FIELD),
            inp.get(t1s.DBP_SELECTIONCOLS),
            aux] if arg != None])
        tag.replace("*", "star")
        return tag    
