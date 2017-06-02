# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        A report generation configuration class
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  11 Sep 2013   SY             Original version
# *****************************************************************

# SPAR imports:
import spar_python.report_generation.common.regression as regression
import spar_python.report_generation.common.config as config
import spar_python.report_generation.ta2.ta2_database as t2d
import spar_python.report_generation.ta2.ta2_schema as t2s

class Ta2Config(config.Config):
    """Represents a configuration object.

    Additional Attributes:
        var_depth: the variable name for circuit depth
        var_batchsize: the variable name for the batch size
        var_numbatches: the variable name for the number of batches
        var_latency: the variable name for latency
        baaratio: the value r for which the performers have to meet
            performer_evallatency <= baseline_evallatency*r
        tanum: the number of the technical area (should be 2)
        keygenlatency: function to be regressed for computing key generation
            latency based on various parameters
        keygenlatency_str: the string representing keygenlatnecy (should have %s
            for each regression parameter)
        encryptionlatency: function to be regressed for computing encryption
            latency based on various parameters
        encryptionlatency_str: the string representing encryptionlatnecy
            (should have %s for each regression parameter)
        evallatency: function to be regressed for computing circuit evaluation
            latency based on various parameters
        evallatency_str: the string representing evallatency (should have %s
            for each regression parameter)
        complexevallatency: function to be regressed for computing circuit
            evaluation latency based on more than two parameters
        complexevallatency_str: the string representing complexevallatency
            (should have %s for each regression parameter)
        desired_sections: a list of sections to be included in the report
    """
    def __init__(self):
        """Initializes the configuration object"""
        super(Ta2Config, self).__init__()
        # variable names for use in graphs:
        self.var_secparam = "K"
        self.var_depth = 'D'
        self.var_batchsize = 'L'
        self.var_numbatches = 'W'
        self.var_latency = 't'
        # other general parameters:
        self.baaratio = 100000
        # per-performer parameters:
        self.__results_db = None
        self.tanum = 2
        self.keygenlatency = None
        self.keygenlatency_str = None
        self.encryptionlatency = None
        self.encryptionlatency_str = None
        self.evallatency = None
        self.evallatency_str = None
        self.desired_sections = [
            "ta2_other_sections",
            "ta2_correctness",
            "ta2_performance",
            "ta2_performance_totalelapsedtime",
            "ta2_performance_keygen",
            "ta2_performance_ingestion",
            "ta2_performance_encryption",
            "ta2_performance_evaluation",
            "ta2_performance_decryption",
            "ta2_performance_singlegatetype",
            "ta2_system_utilization"]
        
    @property
    def keygenlatency_ftr(self):
        """Gives a function to regress object corresponding to the key
        generation latency."""
        return regression.FunctionToRegress(
            self.keygenlatency, self.keygenlatency_str)

    @property
    def encryptionlatency_ftr(self):
        """Gives a function to regress object corresponding to the encryption
        latency."""
        return regression.FunctionToRegress(
            self.encryptionlatency, self.encryptionlatency_str)

    @property
    def evallatency_ftr(self):
        """Gives a function to regress object corresponding to the circuit
        evaluation latency."""
        return regression.FunctionToRegress(
            self.evallatency, self.evallatency_str)

    @property
    def complexevallatency_ftr(self):
        """Gives a function to regress object corresponding to the circuit
        evaluation latency described in terms of more than two variables."""
        return regression.FunctionToRegress(
            self.complexevallatency, self.complexevallatency_str)

    @property
    def results_db(self):
        """Returns the results database."""
        if not self.__results_db:
            self.__results_db = t2d.Ta2ResultsDB(self.results_db_path)
        return self.__results_db
    
    def get_constraint_list(self, fields, require_correct=True,
                            usebaseline=False, require_random=False):
        """Returns a constraint list based on the given arguments"""
        constraint_list = []
        pertables = set([
            t2s.PERKEYGEN_TABLENAME, t2s.PERINGESTION_TABLENAME,
            t2s.PEREVALUATION_TABLENAME])
        table_to_pertable = {
            t2s.PARAM_TABLENAME: t2s.PERKEYGEN_TABLENAME,
            t2s.CIRCUIT_TABLENAME: t2s.PERINGESTION_TABLENAME,
            t2s.INPUT_TABLENAME: t2s.PEREVALUATION_TABLENAME}
        present_tables = [tablename for (tablename, fieldname) in fields]
        present_pertables = list(pertables & set(present_tables))
        if present_pertables:
            pertable = present_pertables[0]
        else:
            assert len(list(set(present_tables))) == 1, (
                "More than one table present")
            pertable = table_to_pertable[present_tables[0]]
        performernamefields = {
            t2s.PERKEYGEN_TABLENAME: t2s.PERKEYGEN_PERFORMERNAME,
            t2s.PERINGESTION_TABLENAME: t2s.PERINGESTION_PERFORMERNAME,
            t2s.PEREVALUATION_TABLENAME: t2s.PEREVALUATION_PERFORMERNAME}
        if ((pertable == t2s.PEREVALUATION_TABLENAME) and require_correct):
            constraint_list.append(
                (t2s.PEREVALUATION_TABLENAME, t2s.PEREVALUATION_CORRECTNESS,
                 True))
        if require_random:
            constraint_list.append(
                (t2s.CIRCUIT_TABLENAME, t2s.CIRCUIT_TESTTYPE, "RANDOM"))
        if usebaseline:
            constraint_list.append(
                (pertable, performernamefields[pertable], self.baselinename))                
        else:
            constraint_list.append(
                (pertable, performernamefields[pertable], self.performername))
        return constraint_list
