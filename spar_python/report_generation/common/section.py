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

class Section(object):
    """A report section.
    This is the superclass for the section classes, which are responsible for
    creating LaTeX code for each section of the report.
    """

    def __init__(self, jinja_template, report_generator):
        """
        Initializes the section with a jinja template and a report generator.
        """
        self._jinja_template = jinja_template
        self._report_generator = report_generator
        self._outp = {} # all section-specific information for the template
                        # will be stored here
        self._config = self._report_generator.config

    def _populate_output(self):
        """Populates the output object which is passed to the Jinja tempalte
        in get_string."""
        pass
    
    def get_string(self):
        """Returns the LaTeX string representing the section."""
        self._populate_output()
        string = self._jinja_template.render(
            outp=self._outp, config=self._report_generator.config)
        return string

    def get_img_path(self, inp=None, aux=None):
        """Returns the path for any images associated with this section.

        Args:
            inp: an Input object
            aux: any auxiliary string
        """
        img_path = "".join([
            self._report_generator.config.img_dir,
            os.sep,
            self.get_tag(inp, aux),
            ".png"])
        return img_path

    def write(self, path, content):
        """Creates a file in the specified location with the specified content.
        This is factored out for ease of testing."""
        this_file = open(path, 'w')
        this_file.write(content)
        this_file.close()
        
    def should_be_included(self):
        """Returns True if the section should be included, and False otherwise.
        If a section should not always be included for a specific subclass,
        this method should be overridden in that subclass."""
        return True
