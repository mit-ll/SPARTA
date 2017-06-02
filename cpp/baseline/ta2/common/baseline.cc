//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Sep 2012  yang            Original Version
//*****************************************************************

#include <string>
#include <iostream>
#include "baseline.h"
#include "common/logging.h"
#include "common/check.h"

using namespace std;

Baseline::Baseline(CircuitParser* p) 
  : parser_(std::auto_ptr<CircuitParser>(p)) {
}

void Baseline::InjestCircuit() {
  circuit_ = parser_->ParseCircuit();
  cout << "CIRCUIT\nCIRCUIT READY\nENDCIRCUIT" << endl;
}

void Baseline::StorePublicKey() {
  string line;
  while(line != "ENDKEY") {
    getline(cin, line);
  }
}

// Listen on stdin
void Baseline::Start() {
  string line;
  while (getline(cin, line)) {
    if (line == "KEY") {
      StorePublicKey();
    } else if (line == "CIRCUIT") {
      InjestCircuit();
    } else if (line == "EDATA") {
      ReadInputAndEvaluate();
    } else {
      LOG(FATAL) << "Unexpected input on baseline's stdin: " << line;
    }
  }
}
