//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Interface and some concrete sub-classes for logging Knot
//                     data.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 13 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_GENERAL_LOGGER_H_
#define CPP_COMMON_GENERAL_LOGGER_H_

#include <iostream>
#include <memory>
#include <thread>
#include <mutex>

#include "knot.h"
#include "timer.h"

/// Abstract base class. Subclasses can write logs to files, the network, etc.
/// They may add headers before the logged lines, change the format, etc.
///
/// Note that this is similar to the Log class in logging.h and the
/// OutputHandler class in output-handler.h. However, these are different in the
/// following ways:
///
/// - Log: specific to general logging with WARNING, INFO, DEBUG, etc. Has
/// facilities for efficiently "disappearing" if the current log level is above
/// the level of the log message. Achieves thread safety by buffering messages
/// until they are complete and then writing them out. Does not flush() the
/// output.
///
/// - OutputHandler: originally written for communicating from the SUT to the
/// test harness. Thus messages are always immediately flush'd. Has a facility
/// for ensuring only one OutputHandler per ostream* exists.
///
/// - This class is designed for logging data, particularly timing, in the test
/// harness. It therefore does not call flush as buffering will decrease the
/// impact it has on performance. It does not try to guarantee one logger per
/// stream as it would be find to use one logging mechanism for part of the
/// test and a different mechanism for other parts. Additionally, it provides
/// support for subclasses that can take care of writing out time data,
/// headers, etc. and we might use different subclasses for different parts of
/// the test.
///
/// It is probably worth combining these classes at some point but we don't have
/// the time right now.
///
/// TODO(odain): Combine these classes!
class GeneralLogger {
 public:
  virtual ~GeneralLogger() {}
  /// Subclasses must override these. Note that all implementations must be
  /// thread safe.
  virtual void Log(const Knot& data) = 0;
  virtual void Log(const char* data) = 0;
  virtual void Log(const std::string& data) = 0;
  virtual void Flush() = 0;
};

/// A logger that writes the current time (as accurately as possible) and the
/// data to be logged to an ostream. Subclasses override the GetTime method so
/// they can get the time from different sources.
class OstreamTimeLoggerBase : public GeneralLogger {
 public:
  /// The ostream to which we should log. This sets format flags on the ostream
  /// and it is assumed that no other threads are using the stream at the same
  /// time. This takes ownership of output.
  OstreamTimeLoggerBase(std::ostream* output);
  /// The same as the above but the owns_stream booloean indicates if this should
  /// free the ostream* in it's destructor. This is handy if you want to log to a
  /// stream like cout or cerr.
  OstreamTimeLoggerBase(std::ostream* output, bool owns_stream);
  OstreamTimeLoggerBase(std::ostream* output, bool owns_stream, bool unbuffered);
  virtual ~OstreamTimeLoggerBase();

  virtual void Log(const Knot& data);
  virtual void Log(const char* data);
  virtual void Log(const std::string& data);
  void Flush();

 protected:
  virtual double GetTime() = 0;
  
 private:
  /// Assumes output_tex_ is held! The elapsed time is passed as we generally
  /// want to get that *before* we aquire the mutex so the timing data is
  /// accurate.
  void LogHeader(double elapsed);
  /// Does the non-tivial constructor work.
  void Setup();
  void UnguardedFlush();

  std::auto_ptr<std::ostream> output_;
  /// If this is true we'll release() the stream in the destructor instead of
  /// freeing it.
  bool owns_stream_;
  /// If this is true, we'll Flush() the stream after every Log().
  bool unbuffered_;
  std::mutex output_tex_;
};

/// Returns the time since the logger was constructed.
class OstreamElapsedTimeLogger : public OstreamTimeLoggerBase {
 public:
  OstreamElapsedTimeLogger(std::ostream* output)
      : OstreamTimeLoggerBase(output) { timer_.Start(); }
  /// The same as the above but the owns_stream booloean indicates if this should
  /// free the ostream* in it's destructor. This is handy if you want to log to a
  /// stream like cout or cerr.
  OstreamElapsedTimeLogger(std::ostream* output, bool owns_stream)
      : OstreamTimeLoggerBase(output, owns_stream) { timer_.Start(); }
  OstreamElapsedTimeLogger(
      std::ostream* output, bool owns_stream, bool unbuffered)
      : OstreamTimeLoggerBase(output, owns_stream, unbuffered) { 
        timer_.Start(); 
      }
  virtual ~OstreamElapsedTimeLogger() {}

  protected:
    virtual double GetTime();

 private:
  /// Does not need to be protected. It maintains no mutable state and is
  /// re-entrant.
  Timer timer_;
};

/// Returns a monotoncially increasing time that doesn't have any particular
/// meaning but it guaranteed to be consistent across process, threads, etc. This
/// is a global hardware counter.
class OstreamRawTimeLogger : public OstreamTimeLoggerBase {
 public:
  OstreamRawTimeLogger(std::ostream* output)
      : OstreamTimeLoggerBase(output) {}
  /// The same as the above but the owns_stream booloean indicates if this should
  /// free the ostream* in it's destructor. This is handy if you want to log to a
  /// stream like cout or cerr.
  OstreamRawTimeLogger(std::ostream* output, bool owns_stream)
      : OstreamTimeLoggerBase(output, owns_stream) {}
  OstreamRawTimeLogger(
      std::ostream* output, bool owns_stream, bool unbuffered)
      : OstreamTimeLoggerBase(output, owns_stream, unbuffered) {}
  virtual ~OstreamRawTimeLogger() {}

  protected:
    virtual double GetTime();
};

#endif
