# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            MZ
#  Description:        Class for testing ta1_graphing
#                      
#                       
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  Aug 5         MZ             Original Version
# 
#             
# **************************************************************

# general imports:
import unittest

# SPAR imports:
import spar_python.report_generation.common.graphing as graphing
import spar_python.report_generation.common.regression as regression

def ARBITRARY_FUNC_3D(x):
    return pow(2,x[0]) + x[1]
ARBITRARY_FUNC_STRING_3D = "2^x + y"
FUNCTION_3D = regression.Function(ARBITRARY_FUNC_3D, ARBITRARY_FUNC_STRING_3D)

def ARBITRARY_FUNC_2D_1(x):
    return x[0]
ARBITRARY_FUNC_STRING_2D_1 = "x"
FUNCTION_2D_1 = regression.Function(ARBITRARY_FUNC_2D_1,
                                    ARBITRARY_FUNC_STRING_2D_1)

def ARBITRARY_FUNC_2D_2(x):
    return x[0]**2
ARBITRARY_FUNC_STRING_2D_2 = "x^2"
FUNCTION_2D_2 = regression.Function(ARBITRARY_FUNC_2D_2,
                                    ARBITRARY_FUNC_STRING_2D_2)

class GrapingTester(unittest.TestCase):

    @unittest.skip("Currently generating error about 'No labeled objects "
                   "found'...appears to be related to legened generation")
    def test_3d_regression(self):
        """
        Tests the construction of the 3 dimensional regression graph
        """
        
        self.assertNotEqual(default_3d(),"")
        
    def test_2d_regression(self):
        """
        Tests the construction of the 2 dimensional regression graph
        """
        
        self.assertNotEqual(default_2d(),"")
                            
    def test_box_plot(self):
        """
        Tests the construction of the box plot
        """
        
        self.assertNotEqual(box(), "")
    def test_percentile(self):
        """
        Tests the construction of the percentile plot
        """
        self.assertNotEqual(perc(),"")

    def test_side_effects(self):
        """
        Makes sure that the order of graphing does not affect the outcome
        """
        box1 = box()
        perc1 = perc()
        two_d_1 = default_2d()
        three_d_1 = default_3d()
        two_d_2 = default_2d()
        perc2 = perc()
        box2 = box()
        three_d_2 = default_3d()
        self.assertEqual(box1,box2)
        self.assertEqual(two_d_1, two_d_2)
        self.assertEqual(three_d_1, three_d_2)
        self.assertEqual(perc1,perc2)

class StubPercentileGetter(object):
    """This is a stub percentile getter class intended only for use with these
    unit tests."""
    def __init__(self, performer_percentiles, baseline_percentiles):
        """Initializes the stub percentile getter with the specified values."""
        self._pp = performer_percentiles
        self._bp = baseline_percentiles
    def get_performer_percentiles(self):
        return self._pp
    def get_baseline_percentiles(self):
        return self._bp
        
def default_2d():
    """
    Returns a simple 2d graph
    """
    return graphing.graph2d("Example title",
                       [([1,2,3,4,5], [1,4,9,16,25],
                         "Some points", FUNCTION_2D_1),
                        ([1,2,3,4,5], [2,5,10,17,26],
                         "More points", FUNCTION_2D_2)],
                       "Inputs", "Outputs")
def default_3d():
    """
    Returns a simple 3d graph
    """
    return graphing.graph3d("Example title",
                       [1,2,3,4,5], [4,2,7,3,1], [6,6,15,19,33],
                       "First input", "Second input", "Output",
                       best_fit_function=FUNCTION_3D)
    
def box():
    """
    Returns a simple box plot
    """
    return graphing.box_plot("Box plot of numbers",
                        [("set1", [2,4,6,3,6,2,5]),
                         ("set2", [3,3,3,2,7,2,5]),
                         ("set3", [2,2,3])])
def perc():
    """
    Returns a simple percentile chart
    """
    percentile_getter = StubPercentileGetter(range(100), range(100))
    return graphing.comparison_percentile_graph(percentile_getter, "latency")

