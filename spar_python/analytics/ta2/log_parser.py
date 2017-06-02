# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            Yang
#  Description:        Parser class for TA2 log files
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  22 Feb 2013   Yang           Original Version
# *****************************************************************

# A LogParser is a raw result log parser for TA2 data.
class LogParser:

    VALID_LABELS = {
            'KEY': ['KEYGEN', 'KEYTRANSMIT', 'KEYSIZE'],
            'CIRCUIT': ['INGESTION', 'CIRCUITTRANSMIT'],
            'INPUT': ['ENCRYPT', 'INPUTTRANSMIT', 'INPUTSIZE', 'EVAL',
                'OUPUTTRANSMIT', 'OUTPUTSIZE', 'DECRYPT', 'DECRYPTED RESULT']
            }

    def __init__(self, log):
        self.__lines = log.strip().split('\n')
        self.__index = 0

    def parse_data(self, action):
        """This function takes as input a string that indicates the next action
        to parse. Valid actions are 'KEY', 'CIRCUIT', and 'INPUT'. By specifying
        'KEY', this function returns a dictionary of (key, value) pairs that
        relate to key generation. By specifying 'CIRCUIT', the function returns
        (key, value) pairs that relate to circuit ingestion. Finally, by
        specifying 'INPUT', the output relates to homomorphic evaluation."""
        assert action == 'KEY' or action == 'CIRCUIT' or action == 'INPUT'
        data = dict.fromkeys(LogParser.VALID_LABELS[action], '')
        num_data = len(LogParser.VALID_LABELS[action])
        for i in xrange(num_data):
            (label, value) = self.__getline()
            if label is not None:
                data[label] = value
        return data
    
    def __getline(self):
        """Returns a (label, data) tuple, where label is a token from the result
        log (ex. EVAL) and data is the value associated with that token. Caling
        this function also advances the pointer to the file buffer to the next
        newline."""
        # line should be of the form 'LABEL: value'
        if self.__index >= len(self.__lines):
            return (None, None)
        line = self.__lines[self.__index]
        tokens = line.split(':')
        self.__index += 1
        return (tokens[0], tokens[1].strip())
