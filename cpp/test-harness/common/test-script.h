//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A TestScript class. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_TEST_SCRIPT_H_
#define CPP_TEST_HARNESS_COMMON_TEST_SCRIPT_H_

#include "common/logging.h"
#include "common/future.h"
#include "common/knot.h"
#include "common/line-raw-data.h"

/// A test script is a pure virtual base class that provides a common interface
/// for all tests. Generally there will be a subclass for each test "type" and
/// then each type may be instantiated multiple times with different parameters.
/// For example, there might be a QueryLatencyTestScript subclass that measures
/// query latency. It could be instantiated multiple times with a different set
/// of queries in order to measure latencies for simple and complex queries.
class TestScript {
 public:
  TestScript() {}
  virtual ~TestScript() {}
  /// Sublcasses must implement this method.
  virtual void Run() = 0;

  /// Same as Run() but fires the passed Future (and sets it to true) when Run()
  /// completes. This allows you to monitor a script running in another thread
  /// for completion.
  void Run(Future<bool> f) {
    Run();
    f.Fire(true);
  }

  /// Runs the script in a thread and returns a Future that fires when the script
  /// is complete. The future fires with true if Run() ran to the end and it
  /// fires with false if Terminate() interrupted the script before Run()
  /// completed.
  Future<bool> RunInThread();

  /// Scripts may optionally implement this method if they can be interrupted
  /// mid-run.
  virtual void Terminate() {
    /// Most don't do this so we provide a default implmentation.
    LOG(FATAL) << "This script doesn't provide a Terminate() method.";
  }
};

#endif
