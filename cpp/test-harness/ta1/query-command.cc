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
#include "query-command.h"

#include <functional>
#include <memory>

#include "test-harness/common/agg-numbered-command-sender.h"
#include "test-harness/common/generic-log-message-formats.h"
#include "test-harness/common/event-message-monitor.h"
#include "common/general-logger.h"
#include "row-hash-aggregator.h"
#include "common/string-algo.h"

Future<Knot> QueryCommand::Schedule(int local_id, uint64_t query_id, 
                                    const Knot& data, GeneralLogger* logger) {
  // The length of the string "SELECT "
  const int kSelectLen = 7;
  CHECK(data.StartsWith("SELECT ", kSelectLen));
  // The command needs to end with a line feed.
  DCHECK(*(data.LastCharIter()) == '\n');

  std::unique_ptr<RowHashAggregator> agg(new RowHashAggregator);
  Future<Knot> f = agg->GetFuture();
  Knot desc_message;
  int global_id;

  desc_message.AppendOwned("QID ", 4);
  LOG(DEBUG) << "Scheduling query id: " << query_id;
  LOG(DEBUG) << "Converting query id to: " 
             << ConvertNumeric<uint64_t>(query_id);
  desc_message.Append(new std::string(ConvertNumeric<uint64_t>(query_id)));
  desc_message.AppendOwned(": [[", 4);
  desc_message.Append(data.SubKnot(data.begin(), data.LastCharIter()));
  desc_message.AppendOwned("]]", 2);

  logger->Log(CommandQueuedMessage(local_id));

  nc_sender_->SendCommand(data, std::move(agg), &global_id,
                          LogNumberedCommandSent(logger, 
                                                 local_id, 
                                                 desc_message),
                          LogEventMessage(logger, local_id));

  f.AddCallback(
      std::bind(&QueryCommand::CommandComplete, this, global_id, local_id,
                std::placeholders::_1, logger));

  return f;
}

void QueryCommand::CommandComplete(int global_id, int local_id, 
                                   const Knot& results, GeneralLogger* logger) {
  logger->Log(CommandCompleteMessageWithNewline(global_id, local_id, results));
}
