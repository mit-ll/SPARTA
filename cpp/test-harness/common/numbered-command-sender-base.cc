//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of NumberedCommandSenderBase. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#include "numbered-command-sender-base.h"

#include <sstream>
#include <string>

#include "numbered-command-counter.h"
#include "event-message-monitor.h"
#include "ready-monitor.h"

using std::string;

const char NumberedCommandSenderBase::kCommandHeader[] = "COMMAND ";
const int NumberedCommandSenderBase::kCommandHeaderLen =
    strlen(NumberedCommandSenderBase::kCommandHeader);
const char NumberedCommandSenderBase::kCommandEnd[] = "ENDCOMMAND\n";
const int NumberedCommandSenderBase::kCommandEndLen =
    strlen(NumberedCommandSenderBase::kCommandEnd);

const char NumberedCommandSenderBase::kResultsHeader[] = "RESULTS ";
const int NumberedCommandSenderBase::kResultsHeaderLen =
    strlen(NumberedCommandSenderBase::kResultsHeader);
const char NumberedCommandSenderBase::kResultsEnd[] = "ENDRESULTS";
const int NumberedCommandSenderBase::kResultsEndLen =
    strlen(NumberedCommandSenderBase::kResultsEnd);

void NumberedCommandSenderBase::OnProtocolStart(Knot start_line) {
  DCHECK(start_line.StartsWith(kResultsHeader, kResultsHeaderLen));
  Knot command_id_knot = start_line.SubKnot(
      start_line.IteratorForChar(kResultsHeaderLen), start_line.end());
  int command_id = atoi(command_id_knot.ToString().c_str());
  CHECK(command_id >= 0);

  OnProtocolStartImpl(command_id);
}

void NumberedCommandSenderBase::LineReceived(Knot line) {
  if (line.Equal(kResultsEnd, kResultsEndLen)) {
    ResultsDone();
  } else {
    LineReceivedImpl(line);
  }
}

int NumberedCommandSenderBase::GetNextCommandId() {
  return NumberedCommandCounter::Increment();
}

int NumberedCommandSenderBase::Send(Knot data, 
                                    SentCallback cb,
                                    EventCallback eb) {
  std::ostringstream header_line;
  int command_id = GetNextCommandId();
  // TODO(njhwang) This will silently proceed if an event monitor is defined but
  // no valid callback is passed, or vice versa. Probably fine, but would be
  // better if this gave more helpful error messages/warnings.
  if (event_monitor_ != nullptr && eb != nullptr) {
    event_monitor_->RegisterCallback(command_id, eb);
    LOG(DEBUG) << "Registered event callback for command " << command_id;
  }
  header_line << kCommandHeader << command_id << "\n";

  // TODO(odain): This takes a Knot, not a Knot*, and then copies it (at cost
  // O(m) where m == the # of strands so probably not too expensive) into the
  // Knot* for sending. Consider taking a Knot* and adding a Strand subclass
  // that holds a Knot*. That way the append would be O(1).
  Knot* full_command = new Knot(new string(header_line.str()));
  full_command->Append(data);
  full_command->AppendOwned(kCommandEnd, kCommandEndLen);

  // cb might be an empty callback in which case we pass that all the way down
  // to the ReadyMonitor. However, if it's not null we create a lambda to call
  // it since we need to bind the command_id.
  std::function<void ()> to_call;
  if (cb) {
    to_call = [command_id, cb](){ cb(command_id); };
  }
  ready_monitor_->ScheduleSend(full_command, to_call);

  return command_id;
}
