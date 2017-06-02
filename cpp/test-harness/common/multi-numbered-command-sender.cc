//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of MultiNumberedCommandSender 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 30 Aug 2012   omd            Original Version
//*****************************************************************

#include "multi-numbered-command-sender.h"

#include <cstring>
#include <sstream>
#include <string>

#include "common/string-algo.h"

using std::string;
using std::map;

MultiNumberedCommandSender::MultiNumberedCommandSender(
    ReadyMonitor* ready_monitor, EventMessageMonitor* event_monitor)
    : NumberedCommandSenderBase(ready_monitor, event_monitor) {
}

MultiNumberedCommandSender::~MultiNumberedCommandSender() {
  CHECK(pending_callbacks_.size() == 0)
      << "Destroying MultiNumberedCommandSender "
      << "when there are still outstanding commands.";
}

void MultiNumberedCommandSender::SendCommand(Knot data, 
                                             ResultCallback cb, 
                                             int* command_id, 
                                             SentCallback sb,
                                             EventCallback eb) {
  // If the mutex is not held before Send(), there is a chance that a recipient
  // will receive data, process it, and send data back to this sender, which
  // would trigger OnProtocolStart() and possibly drive the protocol to
  // completion before the callback is even registered, thereby precluding the
  // callback from getting executed and creating unexpected results (and also
  // leaving uncalled callbacks in pending_callbacks_ when this sender gets
  // destroyed).  We therefore lock the mutex before data is sent to guarantee
  // that the transmission of data and the registration of callbacks both occur
  // before the protocol continue.
  MutexGuard g(data_tex_);
  *command_id = Send(data, sb, eb);

  pending_callbacks_.insert(std::make_pair(*command_id, cb));
}

void MultiNumberedCommandSender::OnProtocolStartImpl(int command_id) {
  CHECK(cur_results_data_.get() == NULL);
  cur_results_data_.reset(new NumberedCommandResult); 
  cur_results_data_->command_id = command_id;
  CHECK(cur_results_data_->command_id >= 0);
}

void MultiNumberedCommandSender::ResultsDone() {
  CHECK(cur_results_data_.get() != NULL);
  map<int, ResultCallback>::iterator i;
  ResultCallback cb_to_call;
  {
    MutexGuard g(data_tex_);
    // Find and fire the future with all the data.
    i = pending_callbacks_.find(cur_results_data_->command_id);
    CHECK(i != pending_callbacks_.end())
        << "Received an ENDRESULTS for command: "
        << cur_results_data_->command_id;
    cb_to_call = i->second;
  }
  // Call the callback function.
  cb_to_call(cur_results_data_);
  cur_results_data_.reset();
  Done();
}

void MultiNumberedCommandSender::LineReceivedImpl(Knot line) {
  CHECK(cur_results_data_.get() != NULL);
  cur_results_data_->results_received.AddLine(line);
}

void MultiNumberedCommandSender::RemoveCallback(int command_id) {
  MutexGuard g(data_tex_);
  map<int, ResultCallback>::iterator i = pending_callbacks_.find(command_id);
  CHECK(i != pending_callbacks_.end())
      << "No callback pending for command: " << command_id;
  pending_callbacks_.erase(i);
}

void MultiNumberedCommandSender::RawReceivedImpl(Knot data) {
  CHECK(cur_results_data_.get() != NULL);
  cur_results_data_->results_received.AddRaw(data);
}
