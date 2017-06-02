//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementaton of VerifyCommand 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
//*****************************************************************

#include <algorithm>
#include <cstring>

#include "verify-command.h"

void VerifyCommand::GetCommand(const LineRawData<Knot>& data,
                               Knot* output) {
  // Data should contain just the id of the row to be verified.
  CHECK(data.Size() == 1);
  // Make sure the line is just digits (e.g. a row id)
  Knot row_id = data.Get(0);
  DCHECK(std::all_of(row_id.begin(), row_id.end(),
                     [](const char c) { return isdigit(c); }));
  static const char kVerifyStr[] = "VERIFY ";
  static const int kVerifyStrLen = strlen(kVerifyStr);
  output->AppendOwned(kVerifyStr, kVerifyStrLen);
  output->Append(row_id);
  output->AppendOwned("\n", 1);
}
