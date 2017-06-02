//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of UpdateCommand.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************
#include "update-command.h"

#include <string>

using namespace std;

void UpdateCommand::GetCommand(const LineRawData<Knot>& data,
                               Knot* output) {
  // data must have at least a row ID, a field to update, and an update value.
  DCHECK(data.Size() >= 3);
  // data must have one row ID followed by pairs of field names/update values,
  // and should therefore have an odd number of rows.
  DCHECK((data.Size() % 2) == 1);
  // Row ID must be a line data item.
  DCHECK(!data.IsRaw(0));
  // All field names must be line data items.
#ifdef NDEBUG
  for (unsigned int i = 1; i < data.Size(); i += 2) {
      CHECK(data.IsRaw(i) == false);
  }
#endif

  // Note that the UPDATE syntax has the row to update on the same line as the
  // UPDATE token, so there is no line feed directly after UPDATE.
  output->Append(new string("UPDATE "));
  data.AppendLineRawOutput(output);
  output->Append(new string("ENDUPDATE\n"));
}
