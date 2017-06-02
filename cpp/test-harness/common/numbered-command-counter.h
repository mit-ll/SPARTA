//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A unique ID assigner for all numbered commands in the
//                     same executable. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_NUMBERED_COMMAND_COUNTER_H_
#define CPP_TEST_HARNESS_COMMON_NUMBERED_COMMAND_COUNTER_H_

#include <atomic>

class NumberedCommandFixture;

/// There is more than one class that implements NumberedCommands, but we require
/// global ordering of the command numbers. Thus we use this singleton to ensure
/// that each command gets a unique id.
class NumberedCommandCounter { 
 public:
  /// Atomically increment the value and return the old value.
  static int Increment() {
    return instance_->counter_.fetch_add(1);
  }

 private:
  /// This should only be used by unit tests. Unit tests expect the 1st command
  /// sent in the test to be command 0 so they need a way to reset this.
  /// NumberedCommandFixture, which should probably be used for all numbered
  /// command tests, will call this method to reset things in it's constructor so
  /// the rest of the test doesn't need to worry about it.
  static void Reset() {
    instance_->counter_.store(0);
  }
  friend class NumberedCommandFixture;
  friend class AggNumberedCommandFixture;
  friend class AggNumberedCommandWithEventMonitorFixture;

  /// So this class can't be constructed. It can only be access via the static
  /// get() method. This ensures there is only 1 instance per executable (e.g.
  /// it's a singleton).
  NumberedCommandCounter() : counter_(0) {}
  virtual ~NumberedCommandCounter() {}

  friend void InitialzeNumberedCommandCounter();
  friend void FinalizeNumberedCommandCounter();

  /// Pointer to the one true instance.
  static NumberedCommandCounter* instance_;

  std::atomic<int> counter_;
};

#endif
