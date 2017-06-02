//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of UnsubscribeCommand 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "unsubscribe-command.h"

#include <string>

using namespace std;

void UnsubscribeCommand::GetCommand(const LineRawData<Knot>& data,
                               Knot* output) {
  DCHECK(data.Size() == 1);
  DCHECK(data.IsRaw(0) == false);

  output->Append(new string(GetCommandName() + " "));
  output->Append(data.Get(0));
  output->Append(new string("\n"));
}
