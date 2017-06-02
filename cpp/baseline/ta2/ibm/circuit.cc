//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of CircuitParser 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012  yang            Original Version
//*****************************************************************

#include "circuit.h"
#include "common/check.h"
#include "common/string-algo.h"

using namespace std;

BitArray Circuit::Evaluate(const string& input) {
  output_gate_->Reset();
  Parse(input);
  return output_gate_->Evaluate();
}

void Circuit::Parse(const string& input) {
  unsigned int wire_index = 0;
  int bit_index = 0;
  BitArray bitset(length_);
  // Read for bits and ignore the rest
  for (unsigned int i = 0; i < input.size(); ++i) {
    if (input[i] == '1' || input[i] == '0') {
      if (input[i] == '1')
        bitset[bit_index] = 1;
      if (input[i] == '0')
        bitset[bit_index] = 0;
      ++bit_index;
      if (bit_index == length_) {
        wires_->at(wire_index)->SetInput(bitset);
        DCHECK(wires_->at(wire_index)->Evaluate() == bitset);
        ++wire_index;
        bitset.reset();
        bit_index = 0;
      }
    }
  }
  CHECK(wire_index == wires_->size()) << "Wire index is " << wire_index 
      << ". Expected " << wires_->size();
}

