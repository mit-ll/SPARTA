//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        An RAII-style class for atomically outputting LineRaw
//                     formatted data to an OutputHandler.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_LINE_RAW_TO_OUTPUT_HANDLER_H_
#define CPP_COMMON_LINE_RAW_TO_OUTPUT_HANDLER_H_

#include <string>

#include "output-handler.h"

/// A class that allows you to atomically write out LineRaw formatted
/// data. Call Start() on the class to obtain the mutex. It is illegal to write
/// any output before Start() has been called. Then you can write output with
/// calls to Line(), Raw(), LinePart(), etc. When Stop() is called the output
/// stream is flushed, and the mutex is released.
class LineRawToOutputHandler {
 public:
  LineRawToOutputHandler(OutputHandler* handler);
  virtual ~LineRawToOutputHandler();
  void Start();
  void Stop();
  void Line(const std::string& line);
  void Raw(const std::string& raw);
  void Raw(const char* data, unsigned int length);
  
  template <class T>
  LineRawToOutputHandler& LinePart(const T& data);
  
  void LineDone();
 private:
  OutputHandler* handler_;
  bool lock_obtained_;
};

////////////////////////////////////////////////////////////////////////////////
// Template function definitions
////////////////////////////////////////////////////////////////////////////////

template<class T>
LineRawToOutputHandler& LineRawToOutputHandler::LinePart(const T& data) {
  *handler_ << data;
  return *this;
}


#endif
