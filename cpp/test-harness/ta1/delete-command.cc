//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of DeleteCommand 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************
#include "delete-command.h"

#include <string>

using namespace std;

void DeleteCommand::GetCommand(const LineRawData<Knot>& data,
                               Knot* output) {
  // data must only have one item.
  DCHECK(data.Size() == 1);
  // Row ID must be a line data item.
  DCHECK(!data.IsRaw(0));

  // Note that the DELETE syntax has the row to delete on the same line as the
  // DELETE token, so there is no line feed directly after DELETE.
  output->Append(new string("DELETE "));
  data.AppendLineRawOutput(output);
}
