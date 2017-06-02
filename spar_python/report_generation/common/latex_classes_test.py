# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY, KH
#  Description:        LaTeX floating object classes test
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  24 Jul 2013   SY             Original Version
# *****************************************************************

# general imports:
import unittest
import os

# SPAR imports:
import spar_python.report_generation.common.latex_classes as lc

class TestLatexClasses(unittest.TestCase):

    def test_process_for_latex(self):
        self.assertEqual(lc.process_for_latex("P6"), "Psix")
        self.assertEqual(lc.process_for_latex("E q"), "Eq")

    def test_table_display(self):
        """Tests the table display functionality."""
        table_caption = "my table"
        table_tag = "my_table"
        table_header = ["a", "b", "c"]
        table = lc.LatexTable(table_caption, table_tag, table_header)
        table.add_content(["a1", "b1", "c1"])
        table.add_content(["a2", "b2", "c2"])
        expected_table_string = r"""\begin{center}
\begin{longtable}{|l|l|l|}
\caption{my table} 
\label{tab:my_table} \\ \hline
a & b & c \\ \hline \hline
\endhead
a1 & b1 & c1\\ \hline
a2 & b2 & c2
\\ \hline
\end{longtable}
\end{center}"""
        self.assertEqual(expected_table_string, table.get_string())

    def test_flipped_table_display(self):
        """Tests the table display functionality of a flipped table"""
        table_caption = "my table"
        table_tag = "my_table"
        table_header = ["a", "b", "c"]
        table = lc.LatexTable(table_caption, table_tag, table_header,
                              flip=True)
        table.add_content(["a1", "b1", "c1"])
        table.add_content(["a2", "b2", "c2"])
        expected_table_string = r"""\begin{center}
\begin{longtable}{|l||l|l|}
\caption{my table} 
\label{tab:my_table} \\ \hline
\endhead
a & a1 & a2\\ \hline
b & b1 & b2\\ \hline
c & c1 & c2
\\ \hline
\end{longtable}
\end{center}"""
        self.assertEqual(expected_table_string, table.get_string())

    def test_clean_table_display(self):
        """Tests the clean table display functionality."""
        table_caption = "my table"
        table_tag = "my_table"
        table_header = ["a", "b", "c"]
        table = lc.LatexCleanTable(table_caption, table_tag, table_header)
        table.add_content(["a1", "b1", "c1"])
        table.add_content(["a2", "b2", "c2"])
        expected_table_string = r"""\begin{center}
\begin{longtable}{lll}
\caption{my table} 
\label{tab:my_table} \\ \hline
\endhead
a & b & c\\
a1 & b1 & c1\\
a2 & b2 & c2
\\ \hline
\end{longtable}
\end{center}"""
        self.assertEqual(expected_table_string, table.get_string())

    def test_clean_flipped_table_display(self):
        """Tests the clean table display functionality of a flipped clean
        table."""
        table_caption = "my table"
        table_tag = "my_table"
        table_header = ["a", "b", "c"]
        table = lc.LatexCleanTable(table_caption, table_tag, table_header,
                                   flip=True)
        table.add_content(["a1", "b1", "c1"])
        table.add_content(["a2", "b2", "c2"])
        expected_table_string = r"""\begin{center}
\begin{longtable}{lll}
\caption{my table} 
\label{tab:my_table} \\ \hline
\endhead
a & a1 & a2\\
b & b1 & b2\\
c & c1 & c2
\\ \hline
\end{longtable}
\end{center}"""
        self.assertEqual(expected_table_string, table.get_string())

    def test_chart_display(self):
        """Tests the chart display functionality."""
        chart_caption = "my chart"
        chart_tag = "my_chart"
        chart_top_header = ["a", "b", "c"]
        chart_left_header = ["1", "2", "3"]
        chart = lc.LatexChart(chart_caption, chart_tag,
                              chart_top_header, chart_left_header)
        chart.add_cell("a", "1", "a1")
        chart.add_cell("c", "2", "c2")
        chart.add_cell("b", "2", "b2")
        expected_chart_string = r"""\begin{table}[H]
\centering
\caption{my chart} 
\label{tab:my_chart}
\begin{tabular}{|l||c|c|c|}
\hline
 & a & b & c \\ \hline \hline
1 & a1 &   &  \\ \hline
2 &   & b2 & c2\\ \hline
3 &   &   &  
\\ \hline
\end{tabular}
\end{table}"""
        self.assertEqual(expected_chart_string, chart.get_string())

    def test_image_display(self):
        """Tests the image display functionality."""
        image_caption = "my image"
        image_tag = "my_image"
        image_path = "./my_image.png"
        image = lc.LatexImage(image_caption, image_tag, image_path)
        expected_image_string = r"""\begin{figure}[H]
\caption{my image}
\label{fig:my_image}
\centering
\includegraphics[scale=0.7]{./my_image.png}
\end{figure}"""
        self.assertEqual(expected_image_string, image.get_string())

    def test_table_bad_row_length(self):
        """Tests that an error is thrown when a row with an incorrect length
        is added to a table."""
        table_caption = "my table"
        table_tag = "my_table"
        table_header = ["a", "b", "c"]
        table = lc.LatexTable(table_caption, table_tag, table_header)
        self.assertRaises(AssertionError, table.add_content,
                          ["a1", "b1", "c1", "d1"])
        self.assertRaises(AssertionError, table.add_content,
                          ["a2", "b2"])

    def test_chart_bad_header(self):
        """Tests that an error is thrown when a cell with incorrect column or
        row headers is added to the chart."""
        chart_caption = "my chart"
        chart_tag = "my_chart"
        chart_top_header = ["a", "b", "c"]
        chart_left_header = ["1", "2", "3"]
        chart = lc.LatexChart(chart_caption, chart_tag,
                              chart_top_header, chart_left_header)
        chart.add_cell("a", "1", "a1")
        self.assertRaises(KeyError, chart.add_cell, "d", "1", "d1")
        self.assertRaises(AssertionError, chart.add_cell, "a", "4", "a4")

    def test_macro_display(self):
        """Tests the macro display functionality."""
        macro_name = "mymacro"
        macro_content = "\mathbb{MACRO}"
        macro = lc.LatexMacro(macro_name, macro_content)
        expected_macro_string = r"\newcommand{\mymacro}{\mathbb{MACRO}\xspace}"
        self.assertEqual(expected_macro_string, macro.get_string())
        
    def test_boolean_display(self):
        """Tests the boolean display functionality."""
        boolean_name = "mybool"
        boolean_value = True
        boolean = lc.LatexBoolean(boolean_name, boolean_value)
        expected_boolean_string = r"""\newif\ifmybool
\mybooltrue"""
        self.assertEqual(expected_boolean_string, boolean.get_string())
