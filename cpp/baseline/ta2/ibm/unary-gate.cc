//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of UnaryGate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Sep 2012  yang            Original Version
//*****************************************************************

#include "unary-gate.h"

BitArray UnaryGate::Evaluate() {
  if (evaluated_) {
    return output();
  } else {
    BitArray output = EvaluateImpl();
    SetOutput(output);
    evaluated_ = true;
    return output;
  }
}

void UnaryGate::AddInput(boost::shared_ptr<Gate> input) {
  input_ = input;
}

void UnaryGate::SetConstant(BitArray constant) {
  constant_ = constant;
}

void UnaryGate::Reset() {
  if (evaluated_) {
    evaluated_ = false;
    input_->Reset();
  }
}
