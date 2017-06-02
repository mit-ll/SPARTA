//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of SubscribeCommand 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "subscribe-command.h"

#include <string>

using namespace std;

void SubscribeCommand::GetCommand(const LineRawData<Knot>& data,
                               Knot* output) {
  DCHECK(data.Size() == 2);
  DCHECK(data.IsRaw(0) == false);
  DCHECK(data.IsRaw(1) == false);

  output->Append(new string(GetCommandName() + " "));
  output->Append(data.Get(0));
  output->Append(new string("\n"));
  output->Append(data.Get(1));
  output->Append(new string("\n"));
}
