//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implemenation of GenericNumberedCommand.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************
#include "generic-numbered-command.h"

#include <functional>

#include "test-harness/common/event-message-monitor.h"
#include "generic-log-message-formats.h"

NumberedCommandSender::ResultsFuture GenericNumberedCommand::Schedule(
    const LineRawData<Knot>& data) {
  Knot command;
  GetCommand(data, &command);
  return command_sender_->SendCommand(command);
}

NumberedCommandSender::ResultsFuture GenericNumberedCommand::Schedule(
    const LineRawData<Knot>& data, 
    GeneralLogger* logger,
    int local_id,
    const std::string& desc) {

  Knot desc_message;
  int global_id;
  Knot command;

  GetCommand(data, &command);
  desc_message.Append(new std::string(desc));

  if (local_id >= 0) {
    logger->Log(CommandQueuedMessage(local_id));
  }
  NumberedCommandSender::ResultsFuture result =
      command_sender_->SendCommand(command, &global_id, 
                                   LogNumberedCommandSent(logger, local_id,
                                                          desc_message),
                                   LogEventMessage(logger, local_id));
  result.AddCallback(
      std::bind(&GenericNumberedCommand::LogResults, 
                std::placeholders::_1, logger, local_id));

  return result;
}

void GenericNumberedCommand::LogResults(
    NumberedCommandSender::SharedResults result, 
    GeneralLogger* logger, int local_id) {
  logger->Log(CommandCompleteMessage(
				     result->command_id, local_id, result->results_received));
  if (result->results_received.Size() > 0 &&
      result->results_received.IsRaw(0) == false) {
    Knot received = result->results_received.Get(0);
    if (received.StartsWith("FAILED")) {
      LOG(WARNING) << "Received FAILED from the SUT: "
                   << result->results_received.LineRawOutput();
    }
  }
}
