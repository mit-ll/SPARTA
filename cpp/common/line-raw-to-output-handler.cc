//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of LineRawToOutputHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 May 2012   omd            Original Version
//*****************************************************************

#include "line-raw-to-output-handler.h"

// Can't use CHECK here because the logging framework uses this...
#include <cassert>

using std::string;

LineRawToOutputHandler::LineRawToOutputHandler(OutputHandler* handler)
    : handler_(handler), lock_obtained_(false) {
}

LineRawToOutputHandler::~LineRawToOutputHandler() {
}

void LineRawToOutputHandler::Start() {
  assert(lock_obtained_ == false);
  handler_->Lock();
  lock_obtained_ = true;
}

void LineRawToOutputHandler::Stop() {
  assert(lock_obtained_ == true);
  handler_->Flush();
  handler_->Unlock();
  lock_obtained_ = false;
}

void LineRawToOutputHandler::Line(const string& line) {
  handler_->WriteLocked(line);
  handler_->WriteLocked("\n");
}

void LineRawToOutputHandler::Raw(const string& raw) {
  *handler_ << "RAW\n" << raw.size() << "\n"
      << raw << "ENDRAW\n";
}

void LineRawToOutputHandler::Raw(const char* data, unsigned int length) {
  *handler_ << "RAW\n" << length << "\n";
  handler_->WriteLocked(data, length);
  *handler_ << "ENDRAW\n";
}

void LineRawToOutputHandler::LineDone() {
  *handler_ << "\n";
}
