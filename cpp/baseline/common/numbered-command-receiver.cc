//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of NumberedCommandReceiver. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 May 2012   omd            Original Version
//*****************************************************************

#include "numbered-command-receiver.h"

#include <boost/bind.hpp>
#include <climits>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <utility>

#include "common/string-algo.h"
#include "common/check.h"

using std::stringstream;
using std::make_pair;
using std::string;
using std::cout;
using std::endl;
using std::map;

const char* END_COMMAND_INDICATOR = "ENDCOMMAND";

////////////////////////////////////////////////////////////////////////////////
// NumberedCommandHandler
////////////////////////////////////////////////////////////////////////////////

void NumberedCommandHandler::WriteResults(const LineRawData<Knot>& data) {
  Knot* results = new Knot;
  results->Append(new string("RESULTS "));
  results->Append(new string(itoa(command_number_)));
  results->AppendOwned("\n", 1);
  data.AppendLineRawOutput(results);
  results->Append(new string("ENDRESULTS\n"));
  SendResults(results);
}

void NumberedCommandHandler::WriteResults(const char* data) {
  Knot* results = new Knot;
  results->Append(new string("RESULTS "));
  results->Append(new string(itoa(command_number_)));
  results->AppendOwned("\n", 1);
  results->AppendOwned(data, strlen(data));
  results->Append(new string("ENDRESULTS\n"));
  SendResults(results);
}

StreamingWriter* NumberedCommandHandler::GetStreamingWriter() {
  StreamingWriter* writer = write_queue_->GetStreamingWriter();
  Knot results;
  results.Append(new string("RESULTS "));
  results.Append(new string(itoa(command_number_)));
  results.AppendOwned("\n", 1);
  writer->Write(results);
  return writer;
}

void NumberedCommandHandler::WriteEvent(int event_id, string* info) {
  Knot* results = new Knot;
  results->Append(new string("EVENTMSG\n"));
  results->Append(new string(itoa(command_number_)));
  results->AppendOwned(" ", 1);
  results->Append(new string(itoa(event_id)));
  if (info != nullptr) {
    results->AppendOwned(" ", 1);
    results->Append(info);
  }
  results->AppendOwned("\n", 1);
  SendResults(results);
}

void NumberedCommandHandler::WriteStreamingEvent(StreamingWriter* writer,
                                                 int event_id, 
                                                 string* info) {
  Knot results;
  results.Append(new string("EVENTMSG\n"));
  results.Append(new string(itoa(command_number_)));
  results.AppendOwned(" ", 1);
  results.Append(new string(itoa(event_id)));
  if (info != nullptr) {
    results.AppendOwned(" ", 1);
    results.Append(info);
  }
  results.AppendOwned("\n", 1);
  writer->Write(results);
}

void NumberedCommandHandler::StreamingWriterDone(StreamingWriter* writer) {
  Knot results;
  results.Append(new string("ENDRESULTS\n"));
  DCHECK(writer != nullptr);
  writer->Write(results);
  delete writer;
}

void NumberedCommandHandler::SendResults(Knot* data) {
  if (!write_queue_->Write(data)) {
    LOG(DEBUG) << "Large result set. Calling WriteWithBlock.";
    write_queue_->WriteWithBlock(data);
  }
}

////////////////////////////////////////////////////////////////////////////////
// NumberedCommandReceiver
////////////////////////////////////////////////////////////////////////////////

NumberedCommandReceiver::NumberedCommandReceiver(
    WriteQueue* write_queue) : output_queue_(write_queue),
    pending_commands_(0), cur_data_(NULL) {
}

NumberedCommandReceiver::~NumberedCommandReceiver() {
   WaitForAllCommands();
}

void NumberedCommandReceiver::AddHandler(
    const string& trigger_token, NCHConstructor handler_constructor) {
  CHECK(handler_map_.find(trigger_token) == handler_map_.end());
  handler_map_[trigger_token] = handler_constructor;
}

void NumberedCommandReceiver::CommandDoneCallback() {
  boost::lock_guard<boost::mutex> l(pending_commands_tex_);
  --pending_commands_;
  if (pending_commands_ == 0) {
    all_commands_done_cond_.notify_all();
  }
}

void NumberedCommandReceiver::WaitForAllCommands() {
  boost::unique_lock<boost::mutex> l(pending_commands_tex_);
  while (pending_commands_ > 0) {
    all_commands_done_cond_.wait(l);
  }
}

int NumberedCommandReceiver::NumPendingCommands() {
  boost::unique_lock<boost::mutex> l(pending_commands_tex_);
  return pending_commands_;
}

void NumberedCommandReceiver::OnProtocolStart(Knot line) {
  CHECK(cur_data_.get() == NULL);
  cur_data_.reset(new LineRawData<Knot>);
  Knot::iterator command_number_it = line.Find(' ');
  CHECK(command_number_it != line.end());
  ++command_number_it;
  CHECK(command_number_it != line.end());

  string number_str = 
      line.SubKnot(command_number_it, line.end()).ToString();
  char* end_number_ptr;
  cur_command_number_ = strtol(number_str.c_str(), &end_number_ptr, 10);
  CHECK(*end_number_ptr == '\0')
      << "Invalid character after number in COMMAND line: "
      << line;
  CHECK(end_number_ptr != number_str) << "Invalid number in COMMAND line: "
      << line;

  CHECK(cur_command_number_ >= 0);
}

void NumberedCommandReceiver::LineReceived(Knot data) {
  if (data == END_COMMAND_INDICATOR) {
    DispatchCommand();
    Done();
  } else {
    CHECK(cur_data_.get() != NULL);
    cur_data_->AddLine(data);
  }
}

void NumberedCommandReceiver::RawReceived(Knot data) {
  CHECK(cur_data_.get() != NULL);
  cur_data_->AddRaw(data);
}

void NumberedCommandReceiver::DispatchCommand() {
  // The token that identifies the command handler should be the 1st token of
  // the 1st bit of data.
  CHECK(cur_data_.get() != NULL);
  CHECK(cur_data_->Size() >= 1);
  CHECK(!cur_data_->IsRaw(0));

  map<const string, NCHConstructor>::iterator constructor_it;
  Knot first_line = cur_data_->Get(0);
  Knot::iterator token_break_it = first_line.Find(' ');
  if (token_break_it == first_line.end()) {
    constructor_it = handler_map_.find(first_line.ToString());
  } else {
    constructor_it = handler_map_.find(
        first_line.SubKnot(first_line.begin(), token_break_it).ToString());
  }
  CHECK(constructor_it != handler_map_.end());
  
  NumberedCommandHandler* handler = constructor_it->second();
  handler->SetCommandDoneCallback(
      boost::bind(&NumberedCommandReceiver::CommandDoneCallback,
                  this));
  handler->SetCommandNumber(cur_command_number_);
  handler->SetWriteQueue(output_queue_);

  pending_commands_tex_.lock();
  ++pending_commands_;
  pending_commands_tex_.unlock();

  handler->Execute(cur_data_.release());
}

