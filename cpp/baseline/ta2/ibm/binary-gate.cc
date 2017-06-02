//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of BinaryGate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Aug 2012   yang           Original Version
//*****************************************************************

#include "binary-gate.h"
#include "common/check.h"

void BinaryGate::AddLeftInput(boost::shared_ptr<Gate> input) {
  CHECK(input != NULL) << "Attempting to assign a null input";
  left_input_ = input;
}

void BinaryGate::AddRightInput(boost::shared_ptr<Gate> input) {
  CHECK(input != NULL) << "Attempting to assign a null input";
  right_input_ = input;
}

BitArray BinaryGate::Evaluate() {
  if (evaluated_) {
    return output();
  } else {
    BitArray output = EvaluateImpl();
    SetOutput(output);
    evaluated_ = true;
    return output;
  }
}
