//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A simple class to monitor that the sut is running. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 04 Dec 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA1_SUT_RUNNING_MONITOR_H_
#define CPP_TEST_HARNESS_TA1_SUT_RUNNING_MONITOR_H_

#include <thread>

#include "common/conditions.h"
#include "common/logging.h"
#include "common/types.h"

/// This class is used to monitor a SUT running under control of the test harness
/// to ensure it doesn't unexcpectedly exit. The SUTShutdown method is generally
/// connected to the EventLoop's EOF callback so it gets notified whent the SUT
/// exits. On construction it assumes the SUT is not expected to exit so if this
/// method gets called it does a LOG(FATAL). However, when the SUT is expected to
/// exit (after a SHUTDOWN command for example) the user can call
/// SetShutdownExpected. After this has been called calls to SUTShutdown
/// LOG(INFO) rather than LOG(FATAL).
class SUTRunningMonitor {
 public:
  SUTRunningMonitor() :
      running_(true), shutdown_expected_(false) {}

  void SUTShutdown() {
    running_.Set(false);
    MutexGuard g(shutdown_expected_tex_);
    if (shutdown_expected_) {
      LOG(INFO) << "SUT sucessfully shut down.";
    } else {
      LOG(FATAL) << "Unexpected shutdown of SUT";
    }
  }

  void SetShutdownExpected(bool value) {
    MutexGuard g(shutdown_expected_tex_);
    shutdown_expected_ = value;
  }

  /// Blocks until the SUT shuts down.
  void WaitForShutdown() {
    running_.Wait(false);
  }

 private:
  SimpleCondition<bool> running_;
  bool shutdown_expected_;
  std::mutex shutdown_expected_tex_;
};


#endif
