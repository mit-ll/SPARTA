//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of StealthBaseline. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 20 Sep 2012  yang            Original Version
//*****************************************************************

#include <iostream>
#include "stealth-baseline.h"
#include "stealth-circuit-parser.h"
#include "circuit.h"
#include "common/check.h"
#include "common/logging.h"
#include "common/string-algo.h"

using namespace std;

StealthBaseline::StealthBaseline(StealthCircuitParser* p) : Baseline(p) {}

// Read the input into a string and evaluate on the stored circuit.
// Even though the output is unencrypted, we respond with a EDATA message
// to remain consistent with how the SUT server behaves.
void StealthBaseline::ReadInputAndEvaluate() {
  string line;
  getline(cin, line);
  int size = SafeAtoi(line.c_str());
  char input[size + 1];
  cin.read(input, size);
  getline(cin, line);
  input[size] = '\0';
  CHECK(line == "ENDEDATA") 
      << "Received unexpected message footer from test-harness: " << line;
  //TODO(yang): the short_circuit argument is currently hard-coded
  bool output = circuit_->Evaluate(input, true);
  cout << "EDATA\n" << 1 << "\n" << output << "ENDEDATA" << endl;
}



