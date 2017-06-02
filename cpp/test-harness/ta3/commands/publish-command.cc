//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of PublishCommand 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "publish-command.h"
#include "test-harness/ta3/ta3-log-message-formats.h"
#include "common/hash-aggregator.h"

#include <string>

using namespace std;

void PublishCommand::GetCommand(const LineRawData<Knot>& data,
                               Knot* output) {
  DCHECK(data.Size() >= 2);
  DCHECK(data.IsRaw(0) == false);

  output->Append(new string(GetCommandName() + "\nMETADATA\n"));
  output->Append(data.Get(0));
  output->Append(new string("\nPAYLOAD\n"));
  for (size_t i = 1; i < data.Size(); i++) {
    LineRawData<Knot>(data.Get(i), data.IsRaw(i)).AppendLineRawOutput(output);
  }
  output->Append(new string("ENDPAYLOAD\n"));
  output->Append(new string("END" + GetCommandName() + "\n"));
}

void PublishCommand::LogCommandDesc(
    int global_id, int local_id, const LineRawData<Knot>& data, 
    GeneralLogger* logger) {
  DCHECK(data.Size() >= 2);
  DCHECK(data.IsRaw(0) == false);
  HashAggregator payload_agg;
  Knot metadata = data.Get(0);
  size_t payload_len = 0;
  for (size_t i = 1; i < data.Size(); i++) {
    Knot payload_line= data.Get(i);
    payload_len += payload_line.Size();
    payload_agg.AddPartialResult(payload_line);
  }
  payload_agg.Done();
  logger->Log(PublishCommandSentMessage(global_id, payload_len,
        metadata, payload_agg.GetFuture().Value()));
}
