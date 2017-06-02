//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of NumberedCommandSender 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 30 Aug 2012   omd            Original Version
//*****************************************************************

#include "numbered-command-sender.h"

#include <functional>
#include <cstring>
#include <sstream>
#include <string>

#include "common/string-algo.h"
#include "event-message-monitor.h"
#include "ready-monitor.h"

using std::string;
using std::map;

NumberedCommandSender::NumberedCommandSender(
    ReadyMonitor* ready_monitor, 
    EventMessageMonitor* event_monitor)
    : MultiNumberedCommandSender(ready_monitor, event_monitor) {
}

NumberedCommandSender::ResultsFuture
      NumberedCommandSender::SendCommand(Knot data, 
                                         int* command_id,
                                         SentCallback sb,
                                         EventCallback eb) {

  ResultsFuture results_future;

  MultiNumberedCommandSender::SendCommand(
      data, std::bind(&NumberedCommandSender::ResultsAvailable,
                      this, std::placeholders::_1, results_future),
      command_id, sb, eb);

  return results_future;
}

NumberedCommandSender::ResultsFuture NumberedCommandSender::SendCommand(
    Knot data) {
  int to_discard;
  return SendCommand(data, &to_discard, nullptr, nullptr);
}

void NumberedCommandSender::ResultsAvailable(SharedResults results,
                                             ResultsFuture future) {
  RemoveCallback(results->command_id);
  future.Fire(results);
}
