//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Main executable for IBM baseline 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Sep 2012  yang            Original Version
//*****************************************************************

#include "ibm-circuit-parser.h"
#include "ibm-baseline.h"
#include "common/statics.h"

int main(int argc, char** argv) {
  Initialize();
  IbmBaseline baseline(new IbmCircuitParser());
  baseline.Start();
  return 0;
}

