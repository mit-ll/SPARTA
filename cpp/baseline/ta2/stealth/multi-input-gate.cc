//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    Implementation of MultiInputGate.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 June 2012  yang           Original Version
//****************************************************************

#include "multi-input-gate.h"
#include "../../../common/check.h"

void MultiInputGate::AddInput(GatePtr input) {
  inputs_.push_back(input);
}

GatePtr MultiInputGate::GetInput(int i) {
  return inputs_[i];
}

bool MultiInputGate::Evaluate(bool short_circuit) {
  if (evaluated_) {
    // output is cached
    return output_;
  }
  output_ = EvaluateImpl(short_circuit);
  evaluated_ = true;
  return output_;
}

void MultiInputGate::Reset() {
  if (evaluated_) {
    for (unsigned int i = 0; i < inputs_.size(); ++i) {
      inputs_[i]->Reset();
    }
    evaluated_ = false;
  }
}

int MultiInputGate::NumInputs() {
  return inputs_.size();
}
