//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Stealth circuit parser 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_STEALTH_CIRCUIT_PARSER_H_
#define CPP_BASELINE_TA2_STEALTH_CIRCUIT_PARSER_H_

#include <string>
#include <memory>
#include <istream>

#include "baseline/ta2/common/circuit-parser.h"

class Circuit;

class StealthCircuitParser : public CircuitParser {
 public:
  // Parses the description of a Stealth circuit given as a string and returns 
  // a Circuit object matching the description. For more information on the 
  // specific syntax of the circuit description, refer to the Test Plan.
  virtual std::auto_ptr<Circuit> ParseCircuit(const std::string& input);

  // Parses the description of a Stealth circuit given on stdin and returns 
  // a Circuit object matching the description.
  virtual std::auto_ptr<Circuit> ParseCircuit();
};

#endif
