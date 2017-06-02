//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of logging stuff 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 16 May 2012   omd            Original Version
//*****************************************************************

#include "logging.h"
#include "check.h"
#include "statics.h"

#include <boost/assign/list_of.hpp>
#include <cstdlib>
#include <vector>

using std::string;
using std::vector;

Log::Log(LogLevel level) : log_level_(level) {
  log_msg_stream_ << "[" << LogLevelString(level) << "] ";
}

Log::~Log() {
  log_msg_stream_ << "\n";
  output_handler_->Write(log_msg_stream_.str());
  if (log_level_ == FATAL) {
    exit(1);
  }
}

string Log::LogLevelString(LogLevel level) const {
  static vector<string> levels = boost::assign::list_of("DEBUG")
      ("INFO")("WARNING")("ERROR")("FATAL");
  return levels[level];
}

////////////////////////////////////////////////////////////////////////////////
// Static member initialization
////////////////////////////////////////////////////////////////////////////////

OutputHandler* Log::output_handler_;
LogLevel Log::application_log_level_ = DEBUG;

static void InitDefaultOutputHandler() {
  Log::SetOutputStream(&std::cerr);
}
ADD_INITIALIZER("Logging", &InitDefaultOutputHandler);
ORDER_INITIALIZERS("OutputHandler", "Logging");
