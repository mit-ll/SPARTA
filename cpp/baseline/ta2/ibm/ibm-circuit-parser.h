//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Wrapper for lemon parser 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_CIRCUIT_PARSER_H_
#define CPP_BASELINE_TA2_IBM_CIRCUIT_PARSER_H_

#include <string>
#include <memory>
#include "baseline/ta2/common/circuit-parser.h"

class Circuit;

class IbmCircuitParser : public CircuitParser {
 public:
  // Takes a string in the form of the IBM circuit grammar syntax. Returns a
  // Circuit object that corresponds to the specified string.
  virtual std::auto_ptr<Circuit> ParseCircuit(const std::string& input);

  // Reads the circuit description from stdin and parses it. Stops reading when
  // the scanner hits a linefeed. The circuit description should contain no
  // linefeed characters before the end.
  virtual std::auto_ptr<Circuit> ParseCircuit();
};


#endif
