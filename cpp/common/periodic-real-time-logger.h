//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            ni24039
// Description:        Launches a thread to periodically log the system time
//                     stamp.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Jan 2013   ni24039        Original Version
//*****************************************************************

#ifndef CPP_COMMON_PERIODIC_REAL_TIME_LOGGER_H_
#define CPP_COMMON_PERIODIC_REAL_TIME_LOGGER_H_

#include <memory>
#include <thread>
#include <atomic>

class GeneralLogger;

class PeriodicRealTimeLogger {
 public:
  /// Takes a pointer to a logger, and an integer period in seconds. The
  /// system time will be logged in logger every period_s seconds.
  PeriodicRealTimeLogger(GeneralLogger* logger, unsigned int period_s) :
    logger_(logger), period_s_(period_s), running_(false) {}
  virtual ~PeriodicRealTimeLogger();
  /// Starts the thread that will perform the periodic logging.
  void Start();
  /// Stops the thread that is performing the periodic logging.
  void Stop();

 private:
  GeneralLogger* logger_;
  unsigned int period_s_;
  std::unique_ptr<std::thread> logger_thread_;
  std::atomic<bool> running_;
};

#endif
