//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of AND gate
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   yang           Original Version
//****************************************************************

#include "and.h"
#include "../../../common/check.h"

bool And::EvaluateImpl(bool short_circuit) {
  CHECK(NumInputs() >= 2) << "Not enough inputs";
  bool value = true;
  for (int i = 0; i < NumInputs(); ++i) {
    if (!GetInput(i)->Evaluate(short_circuit)) {
      value = false;
      if (short_circuit) {
        return value;
      }
    }
  }
  return value;
}
