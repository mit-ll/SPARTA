//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        IBM baseline 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Sep 2012  yang            Original Version
//*****************************************************************

#include <iostream>
#include "ibm-circuit-gates.h"
#include "circuit.h"
#include "ibm-circuit-parser.h"
#include "ibm-baseline.h"
#include "common/check.h"
#include "common/logging.h"

using namespace std;

IbmBaseline::IbmBaseline(IbmCircuitParser* p) : Baseline(p) {}

// Read the input into a string and evaluate on the stored circuit.
// Even though the output is unencrypted, we respond with a EDATA message
// to remain consistent with how the SUT server behaves.
void IbmBaseline::ReadInputAndEvaluate() {
  string line;
  // This is the size line
  getline(cin, line);
  int size = atoi(line.c_str());
  char input[size];
  // Read in the specified number of bytes
  cin.read(input, size);
  // This should be the ENDEDATA footer
  getline(cin, line);
  CHECK(line == "ENDEDATA") << "Unexpected input message footer" << line;
  BitArray output = circuit_->Evaluate(input);
  cout << "EDATA\n" << output.size() << "\n" << output << "ENDEDATA" << endl;
}


