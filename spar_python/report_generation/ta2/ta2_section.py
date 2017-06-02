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
import spar_python.report_generation.ta2.ta2_schema as t1s
import spar_python.report_generation.common.section as section

class Ta2Section(section.Section):
    """A report section.
    This is the superclass for the section classes, which are responsible for
    creating LaTeX code for each section of the report.
    """

    def get_tag(self, inp=None, aux=None):
        """Returns the tag for the LaTeX object.
        Attributes are listed in the tag in a canonical order.

        Args:
            inp: an Input object (should be left as none for TA2.)
            aux: any auxiliary string
        """
        tag =  "_".join([str(arg).replace(" ", "") for arg in [
            type(self).__name__,
            aux] if arg != None])
        return tag    
