//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************

#include "clearcache-handler.h"

#include "common/logging.h"
#include "common/write-event-loop.h"

void ClearCacheHandler::OnProtocolStart(Knot start_line) {
  CHECK(start_line == "CLEARCACHE");

  write_queue_->Write(new Knot(new std::string("DONE\n")));
  Done();
}

void ClearCacheHandler::LineReceived(Knot data) {
  LOG(FATAL) << "CLEARCACHE command should be a single line.";
}

void ClearCacheHandler::RawReceived(Knot data) {
  LOG(FATAL) << "CLEARCACHE command should be a single line.";
}
