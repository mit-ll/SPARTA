//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of CircuitParser 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012  yang            Original Version
//*****************************************************************

#include <iostream>
#include "circuit.h"
#include "stealth-def.h"
#include "common/string-algo.h"
#include "common/check.h"


using namespace std;


Circuit::Circuit(ParserState* p) : output_gate_(p->output_gate), 
    wires_(p->wires) {
  delete p;
}

bool Circuit::Evaluate(const string& input, bool short_circuit) {
  output_gate_->Reset();
  Parse(input);
  return output_gate_->Evaluate(short_circuit);
}

void Circuit::Parse(const string& input) {
  unsigned int index = 0;
  // Read for bits and ignore the rest
  for (unsigned int i = 0; i < input.size(); ++i) {
    if (isdigit(input[i])) {
      string bit = input.substr(i, 1);
      int value = SafeAtoi(bit);
      DCHECK(value == 0 || value == 1) 
          << "Value is " << value << " On index " << i;
      wires_->at(index)->SetValue(value);
      ++index;
    } else {
      CHECK(input[i] == ',' || input[i] == ']' || input[i] == '[')
          << "Unexpected character in input file";
    }
  }
  DCHECK(index == wires_->size()) << "Incorrect number of inputs: " << index;
}

