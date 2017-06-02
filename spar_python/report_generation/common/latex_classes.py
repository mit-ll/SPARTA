# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY, KH
#  Description:        LaTeX object classes, which can return LaTeX
#                      code for their representation
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Jul 2013   SY             Original Version
# *****************************************************************

# general imports:
import os
import abc
import string
import re

# The following constants contain all of the formatting for the LaTeX classes.
# Editing the format (e.g. switching from longtable to the regular table
# package) can be done without touching the class code by editing these
# constants.

TABLE_ROWSEP_NOLINE = r"\\"
TABLE_ROWSEP = r"\\ \hline"
TABLE_COLSEP = r" & "
TABLE_NUMROWS_SEP = r"|"

# In TABLE_HEADER_TEMPLATE, the following strings are omitted:
# 1) column_specifier: something of the form |l|l|l|, where the number of c's
# is the number of columns in the table
# 2) caption: the caption for the table
# 3) tag: the latex tag for the table
TABLE_HEADER_TEMPLATE = string.Template(r"""\begin{center}
\begin{longtable}{${column_specifier}}
\caption{${caption}} 
\label{tab:${tag}} \\ \hline""")

# In COLUMN_HEADERS_TEMPLATE, the following strings are omitted:
# 1) column_headers: the table header
COLUMN_HEADERS_TEMPLATE = string.Template(r"${column_headers} \\ \hline \hline")

ENDHEADER = """\endhead"""

TABLE_FOOTER = os.linesep.join([TABLE_ROWSEP, r"\end{longtable}",
                                r"\end{center}"])

# In CHART_HEADER_TEMPLATE, the following strings are omitted:
# 1) column_specifier: something of the form |l|l|l|, where the number of c's
# is the number of columns in the table
# 2) caption: the caption for the table
# 3) tag: the latex tag for the table
# 4) column_headers: the table header
CHART_HEADER_TEMPLATE = string.Template(r"""\begin{table}[H]
\centering
\caption{${caption}} 
\label{tab:${tag}}
\begin{tabular}{${column_specifier}}
\hline
${column_headers} \\ \hline \hline""")

CHART_FOOTER = os.linesep.join([TABLE_ROWSEP, r"\end{tabular}",
                                r"\end{table}"])

# In IMAGE_TEMPLATE, the following strings are omitted:
# 1) caption: the caption for the figure
# 2) tag: the latex tag for the figure
# 3) scale: the scale at which the image should be displayed (a float)
# 4) path: the path to the image
IMAGE_TEMPLATE = string.Template(r"""\begin{figure}[H]
\caption{${caption}}
\label{fig:${tag}}
\centering
\includegraphics[scale=${scale}]{${path}}
\end{figure}""")

# In MACRO_TEMPLATE, the following strings are omitted:
# 1) macro_name: the string used to invoke the LaTeX macro
# 2) macro_content: the LaTeX code that the macro calls
MACRO_TEMPLATE = string.Template(
    r"\newcommand{\${macro_name}}{${macro_content}}")

# In BOOLEAN_TEMPLATE, the following strings are omitted:
# 1) boolean_name: the string used to invoke the LaTeX if statement
# 2) boolean_value: 'true' or 'false'
BOOLEAN_TEMPLATE = string.Template(r"""\newif\if${boolean_name}
\${boolean_name}${boolean_value}""")

def process_for_latex(string):
    """Returns a LaTeX-ready string, without spaces or integers."""
    int_to_str = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
                  5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
    latex_string = string.replace(" ", "")
    lst = re.findall('\d', latex_string)
    for int_str in lst:
        latex_string = re.sub(int_str, int_to_str[int(int_str)], latex_string)
    return latex_string

class LatexFloat:
    """This is the abstract superclass representing a LaTeX float. It is
    extended by classes representing figures, tables, etc.

    Attributes:
        caption: a string that accompanies the float in the LaTeX document
            which is displayed in the resulting pdf document
        tag: a string that accompanies the float in the LaTeX document which
            is not displayed in the pdf document, but which can be used to
            refer to the float from elsewhere in the LaTeX document
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, caption, tag):
        """Initializes the LatexFloat with a caption and a tag."""
        self._caption = caption
        self._tag = tag.replace(" ", "")

    @abc.abstractmethod
    def get_string(self):
        return NotImplemented

class LatexTable(LatexFloat):
    """This is the class representing a LaTeX table.

    The table is a matrix of cells which has a single row of column headers at
    the top, and may have an arbitrary number of content rows following.

    Attributes:
        caption: a string that accompanies the float in the LaTeX document
            which is displayed in the resulting pdf document
        tag: a string that accompanies the float in the LaTeX document which
            is not displayed in the pdf document, but which can be used to
            refer to the float from elsewhere in the LaTeX document
        header: a list containing strings which are to be displayed as the
            first row of the table
        content: a list of lists, each of which contains strings which are to be
            displayed as a content row of the table
        flip: a boolean which, if True, flips the rows and columns 
    """
    def __init__(self, caption, tag, header, flip=False):
        """Initializes the LatexTable with a caption, a tag and a header."""
        super(LatexTable, self).__init__(caption, tag)
        self._header = header
        self._content = []
        self._flip = flip

    @property
    def _num_cols(self):
        if not self._flip:
            return len(self._header)
        else:
            return len(self._content) + 1

    @property
    def _num_rows(self):
        if not self._flip:
            return len(self._content) + 1
        else:
            return len(self._header)

    @property
    def _rows(self):
        if not self._flip:
            return self._content
        else:
            return [[self._content[i][j] for i in xrange(self._num_cols - 1)]
                    for j in xrange(self._num_rows)]
    
    def add_content(self, cont):
        """Adds content to the table.

        Args:
            content: a list of strings representing a table row (of column if
                flip is true).
        """
        if not self._flip:
            assert len(cont) == self._num_cols, (
                "Row of the wrong length added to Table %s" % self._tag)
        else:
            assert len(cont) == self._num_rows, (
                "Col of the wrong length added to Table %s" % self._tag)
        self._content.append(cont)
        
    def get_string(self):
        """Returns LaTeX code representing the table based on the constant
        templates defined."""
        if not self._flip:
            this_column_specifier = TABLE_NUMROWS_SEP + TABLE_NUMROWS_SEP.join(
                ["l" for col in xrange(self._num_cols)]) + TABLE_NUMROWS_SEP
            this_table_header = TABLE_HEADER_TEMPLATE.substitute(
                column_specifier = this_column_specifier,
                caption = str(self._caption),
                tag = str(self._tag))
            this_table_column_headers = COLUMN_HEADERS_TEMPLATE.substitute(
                column_headers = TABLE_COLSEP.join(
                    [str(header_elt) for header_elt in self._header]))
            this_table_content = (TABLE_ROWSEP + os.linesep).join(
                [TABLE_COLSEP.join([str(row_elt) for row_elt in row])
                 for row in self._rows])
            return os.linesep.join([this_table_header,
                                    this_table_column_headers,
                                    ENDHEADER,
                                    this_table_content,
                                    TABLE_FOOTER])
        else:
            this_column_specifier = (
                TABLE_NUMROWS_SEP + "l" + TABLE_NUMROWS_SEP +
                TABLE_NUMROWS_SEP + TABLE_NUMROWS_SEP.join(
                    ["l" for col in xrange(self._num_cols - 1)]) +
                TABLE_NUMROWS_SEP)
            this_table_header = TABLE_HEADER_TEMPLATE.substitute(
                column_specifier = this_column_specifier,
                caption = str(self._caption),
                tag = str(self._tag))
            this_table_content = (TABLE_ROWSEP + os.linesep).join(
                [TABLE_COLSEP.join([header_elt] + [str(elt) for elt in row])
                 for (header_elt, row) in zip(self._header, self._rows)])
            return os.linesep.join([this_table_header,
                                    ENDHEADER,
                                    this_table_content,
                                    TABLE_FOOTER])

class LatexCleanTable(LatexTable):
    """This is the class representing a cleaner LaTeX table,
    with no column or row separators."""

    def get_string(self):
        """Returns LaTeX code representing the table based on the constant
        templates defined."""
        this_column_specifier =  "l" * self._num_cols
        this_column_headers = TABLE_COLSEP.join(
            [str(header_elt) for header_elt in self._header])
        this_table_header = TABLE_HEADER_TEMPLATE.substitute(
            column_specifier = this_column_specifier,
            caption = str(self._caption),
            tag = str(self._tag))
        if self._flip:
            this_table_content = (TABLE_ROWSEP_NOLINE + os.linesep).join(
                [TABLE_COLSEP.join(
                    [self._header[row_num]] + [
                        str(row_elt) for row_elt in self._rows[row_num]])
                 for row_num in xrange(self._num_rows)])
        else:
            this_table_content = (TABLE_ROWSEP_NOLINE + os.linesep).join(
                [TABLE_COLSEP.join(self._header)] + [TABLE_COLSEP.join(
                    [str(row_elt) for row_elt in row]) for row in self._rows])
        return os.linesep.join([this_table_header,
                                ENDHEADER,
                                this_table_content,
                                TABLE_FOOTER])

class LatexChart(LatexFloat):
    """This is the class representing a LaTeX chart.

    The chart is a matrix of cells which has a single row of headers at the top
    and a single column of headers at the left. The rest of the cells are filled
    with 'content'; elements corresponding to all possible combinations of row
    and column headers.

    Attributes:
        caption: a string that accompanies the float in the LaTeX document
            which is displayed in the resulting pdf document
        tag: a string that accompanies the float in the LaTeX document which
            is not displayed in the pdf document, but which can be used to
            refer to the float from elsewhere in the LaTeX document
        top_header: a list containing strings which are to be displayed as the
            first row of the table
        left_header: a list containing strings which are to be displayed as the
            left-most column of the table
        cells: a doubly-nested dictionary mapping combinations of top_header and
            left_header elements to content cells
    """
    def __init__(self, caption, tag, top_header, left_header):
        """Initializes the LatexChart with a caption, a tag, a top_header and a
        left_header."""
        super(LatexChart, self).__init__(caption, tag)
        self._top_header = top_header
        self._num_cols = len(self._top_header)
        self._left_header = left_header
        self._num_rows = len(self._left_header)
        self._cells = {}
        for top_elt in self._top_header:
            self._cells[top_elt] = {}
            for left_elt in self._left_header:
                self._cells[top_elt][left_elt] = " "

    def add_cell(self, top_elt, left_elt, content, color=None):
        """Adds a content cell to the table.

        Args:
            top_elt: the top_header element to which the content cell
                corresponds
            left_elt: the left_header element to which the content cell
                corresponds
            content: the string to be displayed in the content cell
        """
        assert left_elt in self._cells[top_elt], (
            "%s in not a valid row in the chart %s" % (left_elt, self._tag))
        if color:
            this_content = r"\cellcolor{%s}%s" % (color, str(content))
        else:
            this_content = content
            
        self._cells[top_elt][left_elt] = this_content

    def get_string(self):
        """Returns LaTeX code representing the chart based on the constant
        templates defined."""
        this_column_specifier = (
            TABLE_NUMROWS_SEP + "l" + TABLE_NUMROWS_SEP + TABLE_NUMROWS_SEP + 
            TABLE_NUMROWS_SEP.join(["c" for col in xrange(self._num_cols)]) +
            TABLE_NUMROWS_SEP)
        this_column_headers = TABLE_COLSEP.join(
            [""] + [str(top_header_elt) for top_header_elt in self._top_header])
        this_chart_header = CHART_HEADER_TEMPLATE.substitute(
            column_specifier = this_column_specifier,
            caption = self._caption,
            tag = self._tag,
            column_headers = this_column_headers)
        this_chart_content = (TABLE_ROWSEP + os.linesep).join(
            [TABLE_COLSEP.join([str(left_elt)] +
                               [str(self._cells[top_elt][left_elt])
                                for top_elt in self._top_header])
             for left_elt in self._left_header])
        return os.linesep.join([this_chart_header, this_chart_content,
                                CHART_FOOTER])
               
class LatexImage(LatexFloat):
    """This is the class representing a LaTeX image.

    The image is simply an embedding of an external image file, such as a .jpg
    file or a .png file.

    Attributes:
        caption: a string that accompanies the float in the LaTeX document
            which is displayed in the resulting pdf document
        tag: a string that accompanies the float in the LaTeX document which
            is not displayed in the pdf document, but which can be used to
            refer to the float from elsewhere in the LaTeX document
        image_path: a string representing the relative path to the image, such
            as "images/my_image.png".
        scale: a positive float representing the scale at which the image is to
            be displayed. The default value is 1.0.
    """
    def __init__(self, caption, tag, image_path, scale=.7):
        """Initializes the LatexImage with a caption, a tag, an image_path, and
        a scale."""
        super(LatexImage, self).__init__(caption, tag)
        self._image_path = image_path
        self._scale = scale

    def get_string(self):
        """Returns LaTeX code representing the image based on the constant
        templates defined."""
        return IMAGE_TEMPLATE.substitute(
            caption = self._caption,
            tag = str(self._tag),
            scale = str(self._scale),
            path = str(self._image_path))

class LatexMacro(object):
    """This is the class representing a LaTeX macro.

    The macro maps a string to a LaTeX command.

    Attributes:
        macro_name: a string by which the LaTeX command can be invoked
        macro_content: the LaTeX command to which the macro_name string is
            mapped.
    """
    def __init__(self, macro_name, macro_content):
        """Initializes the LatexMacro with a name a content."""
        self._macro_name = process_for_latex(macro_name)
        self._macro_content = macro_content

    def get_string(self):
        """Returns LaTeX code representing the macro based on the constant
        templates defined."""
        return MACRO_TEMPLATE.substitute(
            macro_name = str(self._macro_name),
            macro_content = str(self._macro_content) + r"\xspace")

    def __str__(self):
        return self.get_string()

class LatexBoolean(object):
    """This is the class representing a LaTeX boolean.

    The boolean is represented by a string, and holds a 'true' or 'false' value.

    Attributes:
        boolean_name: a string by which the LaTeX boolean can be invoked
        boolean_value: the value of the boolean
    """
    def __init__(self, boolean_name, boolean_value):
        """Initializes the LatexBoolean with a name and a value."""
        self._boolean_name = process_for_latex(boolean_name)
        self._boolean_value = boolean_value

    def get_string(self):
        """Returns LaTeX code representing the macro based on the constant
        templates defined."""
        boolean_value_string = str(bool(self._boolean_value)).lower()
        return BOOLEAN_TEMPLATE.substitute(
            boolean_name = str(self._boolean_name),
            boolean_value = boolean_value_string)

    def __str__(self):
        return self.get_string()
