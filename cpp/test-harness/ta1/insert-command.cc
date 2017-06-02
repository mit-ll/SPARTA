//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of InsertCommand 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 13 Sep 2012   omd            Original Version
// 19 Sep 2012   ni24039        Refactored to use GenericCommand
//*****************************************************************

#include "insert-command.h"

#include <string>

using namespace std;

void InsertCommand::GetCommand(const LineRawData<Knot>& data,
                               Knot* output) {
  DCHECK(data.Size() > 0);
  DCHECK(data.IsRaw(0) == false);

  output->Append(new string("INSERT\n"));
  data.AppendLineRawOutput(output);
  output->Append(new string("ENDINSERT\n"));
}
