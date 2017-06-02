# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        report generator superclass
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Sep 2013   SY             Original version
# *****************************************************************

# general imports:
import logging
import os

# LOGGER:
LOGGER = logging.getLogger(__file__)

class ReportGenerator(object):
    """Represents a report generator.
    This is the superclass to the TA1 and the TA2 report generators, which are
    responsible for creating LaTeX code for the entire report.

    Attributes:
        config: a configuration object
        jinja_env: a jinja environment
    """

    def __init__(self, config, jinja_env):
        """Initializes the report with a configuration object and a jinja
        environment."""
        self.config = config
        self._jinja_env = jinja_env
        
    def _create_sections(self):
        """Populates the sections attribute."""
        for section_name in self.config.desired_sections:
            (template_name,
             section_class) = self._section_name_to_template_name_and_class[
                 section_name]
            template = self._jinja_env.get_template(template_name)
            this_section = section_class(template, self)
            self._sections.append(this_section)

    def get_string(self):
        """Returns the LaTeX string representing the report."""
        if not self._sections:
            self._create_sections()
        template = self._jinja_env.get_template(self._report_template_name)
        outp = {}
        outp["sections"] = os.linesep.join(
            [section.get_string() for section in self._sections
             if section.should_be_included()])
        string = template.render(outp=outp, config=self.config)
        return string
