//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Main executable to run StealthBaseline. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 20 Sep 2012  yang            Original Version
//*****************************************************************

#include "stealth-circuit-parser.h"
#include "stealth-baseline.h"
#include "common/statics.h"

int main(int argc, char** argv) {
  Initialize();
  StealthBaseline baseline(new StealthCircuitParser());
  baseline.Start();
  return 0;
}
