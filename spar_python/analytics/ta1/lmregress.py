# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            MZ
#  Description:        Regressional analysis tool for testing SPAR
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  29 May 2013   MZ             Original Version
# *****************************************************************

import scipy as sp
import ta1_constants as t1c
import ta1_database as t1db

#Use: Create a RegressionTool instance with the desired fields,
#then run the various functions provided to recieve data about the object


class RegressionTool:

    def __init__(self, newdb, func, newdepvar, checkfunc):
        """
        Constructs a regression tool object

        Takes a ta1_results_db object in newdb and a function in f
        """
        assert isinstance(newdb,t1db.ta1_results_db)
        self.resultsdb = newdb
        self.f = func
        self.depvar = newdepvar #Dependant variable for the regression

    #Optional (user added or future implementation)
        self.guesses = None #Guesses for the rough values of the coefficients
        self.sdeviation = None #Array of standard deviation

    #Data from the sql server. Run update to re-autopopulate these fields
        self.queryresults = None 
        self.columns = {}

    #Organized and formatted data.
        self.inputs = [] #Inner length is the number of tests, outer length is number of variables
        self.inputnames = [] #Contains col#, colname tuples, for later representation
        self.outputs = []

    #Results fields
        self.coefficients = None
        self.covariance = None
        #self.update()

    def __repr__(self):
        return "Coefficients: " + self.coefficients + " Covariance: " + self.covariance

    def update(self):

        ##
        # SQL querying
        ##
        tablinfo = self.resultsdb.execute("PRAGMA table_info (%s)" % t1c.TABLE_NAME)
        for n in range(len(tablinfo)):
            self.columns[tablinfo[n][1]] = n #Put the respective column numbers into a dict for easy access
            self.columns[n] = [tablinfo[n][1]] #TODO: consolidate this with other stuff
        self.resultsdb.execute("SELECT * FROM %s" % t1c.TABLE_NAME) 
        self.queryresults = fetchall()
        ## 
        # Data Organization
        ##
        for row in range(len(queryresults)):
            self.outputs.append(queryresults[row][columns[depvar]])
        
        for fieldnum in range(len(queryresults[0])): 
            varvals = []
            if(self.columns[fieldnum]!=self.depvar):
                inputnames.append((len(inputs),self.columns[fieldnum])) #Tuples to (col#,colname)
                for row in range(len(queryresults)):
                    varvals.append(queryresults[row][fieldnum])
            inputs.append(varvals)
        
                   
    def addguesses(self, newguesses):
        self.guesses = newguesses
                    
    def adddeviation(self, newdev):
        self.sdeviation = newdev

    def run(self):

        self.coefficients, self.covariance = sp.optimize(self.f, self.inputs, self.outputs, self.guesses, self.sdeviation)
