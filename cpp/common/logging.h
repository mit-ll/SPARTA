//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Logging library 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 16 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_LOGGING_H_
#define CPP_COMMON_LOGGING_H_

#include <iostream>
#include <memory>
#include <sstream>
#include <string>

#include "output-handler.h"

/// Defines a set of macros and functions for powerful logging. There aren't a
/// ton of good logging libraries with good licenses, loggers are relatively easy
/// to write, and we might want fine grained control of our logging in order to
/// get accurate timing (e.g. do all logging in a separate thread vs. have each
/// thread write to its own log file so there are no locks, etc.). Having our own
/// library makes it easy to change the implemetation later while keeping the
/// interface consistent.

/// The compiler will elinimate all log calls to levels < MIN_LOG_LEVEL. Other
/// levels may or may not be output depending on the configuration.
#ifndef MIN_LOG_LEVEL
#define MIN_LOG_LEVEL 0
#endif

enum LogLevel {
  DEBUG = 0, INFO = 1, WARNING = 2, ERROR = 3, FATAL = 4
};

class Log {
 public:
  Log(LogLevel level);
  virtual ~Log();

  template<class T>
  Log& operator<<(T data) {
    log_msg_stream_ << data;
    return *this;
  }

  /// TODO(odain) We could override this to be able to set different handlers for
  /// each level.
  static void SetOutputHandler(OutputHandler* handler) {
    output_handler_ = handler;
  }
  static void SetOutputStream(std::ostream* stream) {
    SetOutputHandler(OutputHandler::GetHandler(stream));
  }
  static LogLevel ApplicationLogLevel() {
    return application_log_level_;
  }

  static void SetApplicationLogLevel(LogLevel level) {
    application_log_level_ = level;
  }
 private:
  std::string LogLevelString(LogLevel level) const;
  LogLevel log_level_;

  std::stringstream log_msg_stream_;
  static OutputHandler* output_handler_;
  static LogLevel application_log_level_;
};

/// Two if statements here. The 1st checks against MIN_LOG_LEVEL since that's
/// known at compile time. Thus if level is < MIN_LOG_LEVEL the compiler will
/// completely remove the statement from the binary. The second if compares to
/// the CurrentLevel(), which can be set via command line flags and such. If this
/// if is false none of the operator<< statements execute. Only if both "if"
/// statements evaluate to false does a Log object get constructed and the
/// operator<< functions get called.
#define LOG(level) if (level < MIN_LOG_LEVEL) ; \
    else if (level < Log::ApplicationLogLevel()) ; \
    else Log(level) << __FILE__ << ":" << __LINE__ << " " << __PRETTY_FUNCTION__ << ": "

#endif  // header guard
