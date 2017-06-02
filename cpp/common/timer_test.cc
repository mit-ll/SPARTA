//*****************************************************************
// Copyright 2011 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for Timer class.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Oct 2011   omd            Added this header
//*****************************************************************

#include "timer.h"

#define BOOST_TEST_MODULE TimerTests 

#include <iostream>

#include "test-init.h"

using namespace std;

class TestableTimer : public Timer {
 public:
  virtual ~TestableTimer() {}

  // Makes this protected member public so I can test it.
  static double TestTimespecToDouble(timespec value) {
    return TimespecToDouble(value);
  }
};

BOOST_AUTO_TEST_CASE(TimespecToDoubleCorrect) {
  TestableTimer timer;
  timespec ts;
  // A timespec of 1 millisecond.
  ts.tv_sec = 0;
  ts.tv_nsec = 1000000;
  BOOST_CHECK_EQUAL(timer.TestTimespecToDouble(ts), 0.001);

  // A timespec of 1.01 seconds
  ts.tv_sec = 1;
  ts.tv_nsec = 10000000;
  BOOST_CHECK_EQUAL(timer.TestTimespecToDouble(ts), 1.01);

  // A timespec of 2 seconds excactly
  ts.tv_sec = 2;
  ts.tv_nsec = 0;
  BOOST_CHECK_EQUAL(timer.TestTimespecToDouble(ts), 2);
}

// Make sure our timer has "pretty good" resolution by making sure it can
// accurately time events that are pretty fast. Note that the resolution here is
// a function of the hardware clock resolution and will be different from
// machine to machine. If this test fails that tells us that the machine in
// question might not be a good one to use for testing timing.
BOOST_AUTO_TEST_CASE(TimerResolution) {
  Timer timer;

  // Time something that takes only a few hundred cpu cycles. To make sure
  // the optimizer doesn't optimize away the loop we don't just do a for loop
  // with no body. Instead we compute the sum of a bunch of consecutive
  // integers.
  const int LOOP_SIZE = 100;
  int x = 0;
  timer.Start();
  for (int i = 0; i < LOOP_SIZE; ++i) {
    x += i;
  }
  double elapsed = timer.Elapsed();
  BOOST_CHECK_GT(elapsed, 0);
  // This check is a little dicey as its conceivable that the above loop
  // could take more than 1 second of real time on a severly overloaded and
  // very slow machine but it should be fine.
  BOOST_CHECK_LT(elapsed, 1);
  cout << "Time elapsed: " << elapsed;
  // We have to do something with the computed sum or the optimizer could
  // optimize away the loop.
  BOOST_CHECK_GT(x, 0);
}
