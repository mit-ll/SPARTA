//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of InsertHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 May 2012   omd            Original Version
//*****************************************************************

#include "insert-handler.h"

#include <boost/bind.hpp>
#include <sstream>
#include <string>
#include <memory>
#include <set>

#include "common/ta1-constants.h"
#include "common/schema.h"
#include "common/types.h"
#include "common/check.h"

using std::stringstream;
using std::auto_ptr;
using std::string;
using std::set;

void InsertHandler::Execute(LineRawData<Knot>* command_data) {
  // Do all the work on a separate thread so we can begin handling additional
  // commands as soon as possible. We have DataInserter call InsertDone when
  // it's done.
  DCHECK(command_data != NULL);
  CHECK(command_data->Get(0) == "INSERT");
  CHECK(command_data->Get(command_data->Size() - 1) == "ENDINSERT");
  // Event ID 3: Insert command received
  if (events_enabled_) {
    WriteEvent(3);
  }
  command_data->SetStartOffset(1);
  command_data->SetEndOffset(1);
  std::function<void ()> done_callback =
      std::bind(&InsertHandler::InsertDone, this);
  std::function<void (int, std::string*)> event_callback = nullptr;
  if (events_enabled_) {
    event_callback = 
      std::bind(&NumberedCommandHandler::WriteEvent, this,
                std::placeholders::_1, std::placeholders::_2);
  }
  insert_pool_->AddWork(
      [command_data, done_callback, event_callback](DataInserter* inserter) {
          inserter->PerformInserts(command_data, nullptr, done_callback, event_callback);
      });
}

void InsertHandler::InsertDone() {
  WriteResults("DONE\n");
  Done();
}
