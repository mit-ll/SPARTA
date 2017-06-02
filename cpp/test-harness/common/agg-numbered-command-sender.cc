//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of AggNumberedCommandSender 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#include "agg-numbered-command-sender.h"

#include <utility>

#include "common/aggregating-future.h"
#include "common/string-algo.h"
#include "event-message-monitor.h"

AggNumberedCommandSender::AggNumberedCommandSender(
    ReadyMonitor* ready_monitor,
    EventMessageMonitor* event_monitor) : 
  NumberedCommandSenderBase(ready_monitor, event_monitor),
  cur_agg_(nullptr), 
  cur_command_id_(-1),
  parsing_eventmsg_(false), 
  event_monitor_(event_monitor) {
}

AggNumberedCommandSender::~AggNumberedCommandSender() {
  CHECK(agg_map_.size() == 0) << "Trying to destroy AggNumberedCommandSender "
      << "with outstanding commands.";
}

void AggNumberedCommandSender::SendCommand(
    Knot data, 
    std::unique_ptr<PartialFutureAggregator<Knot>> aggregator,
    int* command_id,
    SentCallback sent_cb, 
    EventCallback event_cb) {
  DCHECK(aggregator.get() != nullptr);
  DCHECK(*data.LastCharIter() == '\n');

  MutexGuard g(data_tex_);
  *command_id = Send(data, sent_cb, event_cb);
  DCHECK(agg_map_.find(*command_id) == agg_map_.end());
  // We can't use a unique_ptr in an STL map so we manually release it here. The
  // main purpose of taking a unique_ptr as a parameter was to clearly document
  // the ownership semantics.
  agg_map_.insert(std::make_pair(*command_id, aggregator.release()));
}

void AggNumberedCommandSender::OnProtocolStartImpl(int command_id) {
  CHECK(cur_agg_ == nullptr);

  MutexGuard g(data_tex_);
  auto map_it = agg_map_.find(command_id);
  CHECK(map_it != agg_map_.end())
      << "No aggregator registered for command: " << command_id;
  cur_agg_ = map_it->second;
  DCHECK(cur_agg_ != nullptr);
  cur_command_id_ = command_id;
}

void AggNumberedCommandSender::LineReceivedImpl(Knot line) {
  MutexGuard g(data_tex_);
  CHECK(cur_agg_ != nullptr);
  if (parsing_eventmsg_) {
    LOG(DEBUG) << "Parsing EVENTMSG info: " << line;
    // Extract the event's command id
    Knot::iterator event_cmd_id_it = line.Find(' ');
    DCHECK(event_cmd_id_it != line.end());
    // Increment the iterator by 1, past the space character
    Knot event_cmd_id_knot = line.Split(++event_cmd_id_it);
    int event_cmd_id = ConvertString<int>(event_cmd_id_knot.ToString());
    LOG(DEBUG) << "Received event message for command " << event_cmd_id;

    // Extract the event id
    Knot::iterator event_id_it = line.Find(' ');
    int event_id = -1;
    if (event_id_it == line.end()) {
      event_id = ConvertString<int>(line.ToString());
      line.Clear();
    } else {
      // Increment the iterator by 1, past the space character
      Knot event_id_knot = line.Split(++event_id_it);
      event_id = ConvertString<int>(event_id_knot.ToString());
    }
    LOG(DEBUG) << "Received event message id " << event_id;

    // Call event callback
    EventCallback eb_callback = event_monitor_->GetCallback(event_cmd_id);
    if (eb_callback != nullptr) {
      eb_callback(event_cmd_id, event_id, line);
    }
    parsing_eventmsg_ = false;
  } else if (line.ToString() == "EVENTMSG") {
    // TODO(njhwang) Should probably change protocol to have command id on same
    // line as EVENTMSG
    LOG(DEBUG) << "Received EVENTMSG token";
    DCHECK(event_monitor_ != nullptr);
    parsing_eventmsg_ = true;
  } else {
    cur_agg_->AddPartialResult(line);
  }
}

void AggNumberedCommandSender::RawReceivedImpl(Knot data) {
  MutexGuard g(data_tex_);
  CHECK(cur_agg_ != nullptr);
  CHECK(!parsing_eventmsg_) << "Raw mode entered before EVENTMSG message "
                            << "fully received";
  cur_agg_->AddPartialResult(data);
}

void AggNumberedCommandSender::ResultsDone() {
  MutexGuard g(data_tex_);
  CHECK(cur_agg_ != nullptr);
  CHECK(!parsing_eventmsg_) << "ENDRESULTS received before EVENTMSG message "
                            << "fully received";
  cur_agg_->Done();

  DCHECK(agg_map_.find(cur_command_id_) != agg_map_.end());
  agg_map_.erase(cur_command_id_);

  delete cur_agg_;
  cur_agg_ = nullptr;
  cur_command_id_ = -1;

  Done();
}
