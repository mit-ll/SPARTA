//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of PeriodicRealTimeLogger
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Jan 2013   ni24039        Original Version
//*****************************************************************

#include "periodic-real-time-logger.h"
#include "general-logger.h"
#include "util.h"

PeriodicRealTimeLogger::~PeriodicRealTimeLogger() {
  Stop();
}

void PeriodicRealTimeLogger::Start() {
  auto logger_fn = [this]() {
    Timer t;
    while (true) {
      t.Start();
      // Otherwise, log the system time stamp and delay for period_s.
      LogRealTime(logger_);
      while (t.Elapsed() < period_s_) {
        // Check if we've requested for the logging to stop.
        if (!running_) {
          return;
        }
      }
    }
  };
  running_ = true;
  logger_thread_.reset(new std::thread(logger_fn));
}

void PeriodicRealTimeLogger::Stop() {
  running_ = false;
  if (logger_thread_) {
    LOG(DEBUG) << "PeriodicRealTimeLogger waiting for logging thread to stop";
    logger_thread_->join();
    logger_thread_.reset();
    LOG(DEBUG) << "PeriodicRealTimeLogger stopped";
  }
}
