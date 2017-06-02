//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    Implementation of XOR gate
// 
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 07 Aug 2012   Yang           Original Version
//****************************************************************

#include "xor.h"
#include "../../../common/check.h"

bool Xor::EvaluateImpl(bool short_circuit) {
  CHECK(NumInputs() >= 2) << "Not enough inputs";
  unsigned int sum = 0;
  for (int i = 0; i < NumInputs(); ++i) {
    if (GetInput(i)->Evaluate(short_circuit)) {
      ++sum;
    }
  }
  return sum % 2;
}


