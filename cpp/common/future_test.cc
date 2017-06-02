//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Unit test for Future class.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Jul 2012   omd            Original Version
//*****************************************************************

#include "future.h"

#define BOOST_TEST_MODULE FutureTest

#include <boost/thread.hpp>
#include <boost/bind.hpp>
#include <string>

#include "test-init.h"
#include "check.h"
#include "conditions.h"

using std::string;

// This is called in a different thread so it can wait for the future and then
// check it's value. The SimpleCondition waititng is set to true just before
// Wait is called on the future. This lets the test thread know that it can fire
// the furture and actually be testing that it wakes the thread.
template<class ResultT>
void WaitAndExpect(Future<ResultT> f, SimpleCondition<bool>* waiting,
                   ResultT expected, bool* called) {
  CHECK(*called == false);
  waiting->Set(true);
  f.Wait();
  BOOST_CHECK_EQUAL(f.Value(), expected);
  *called = true;
}

template<class ResultT>
void CheckExpectedCallback(ResultT expected, ResultT received, bool* called) {
  CHECK(*called == false);
  BOOST_CHECK_EQUAL(received, expected);
  *called = true;
}

BOOST_AUTO_TEST_CASE(WaitWorks) {
  Future<int> f;
  const int kFireValue = 42;
  bool called = false;
  SimpleCondition<bool> thread_waiting(false);

  boost::thread t(&WaitAndExpect<int>, f, &thread_waiting,
                  kFireValue, &called);
  // Wait for the thread to start and call Wait() on the future.
  thread_waiting.Wait(true);
  f.Fire(kFireValue);
  // Wait for the thread to complete.
  t.join();
  // And double check that our function was actually called and it actually
  // returned.
  BOOST_CHECK_EQUAL(called, true);
  // Also check that Value works as expected.
  BOOST_CHECK_EQUAL(f.Value(), kFireValue);
}

// Check that any callbacks that are added before Fire() is called are actually
// called.
BOOST_AUTO_TEST_CASE(CallbacksAddedBeforeFireCalled) {
  Future<int> f;
  const int kFireValue = 107;

  bool cb1_called = false;
  Future<int>::FutureCallback cb1(
      boost::bind(&CheckExpectedCallback<int>, kFireValue, _1, &cb1_called));
  f.AddCallback(cb1);

  bool cb2_called = false;
  Future<int>::FutureCallback cb2(
      boost::bind(&CheckExpectedCallback<int>, kFireValue, _1, &cb2_called));
  f.AddCallback(cb2);

  f.Fire(kFireValue);
  BOOST_CHECK_EQUAL(cb1_called, true);
  BOOST_CHECK_EQUAL(cb2_called, true);
  // Also check that Value works as expected.
  BOOST_CHECK_EQUAL(f.Value(), kFireValue);
}


// Check that any callbacks added after Fire() is called are actually called.
BOOST_AUTO_TEST_CASE(CallbacksAddedAfterFireCalled) {
  Future<int> f;
  const int kFireValue = 107;

  f.Fire(kFireValue);

  bool cb1_called = false;
  Future<int>::FutureCallback cb1(
      boost::bind(&CheckExpectedCallback<int>, kFireValue, _1, &cb1_called));
  f.AddCallback(cb1);

  bool cb2_called = false;
  Future<int>::FutureCallback cb2(
      boost::bind(&CheckExpectedCallback<int>, kFireValue, _1, &cb2_called));
  f.AddCallback(cb2);

  BOOST_CHECK_EQUAL(cb1_called, true);
  BOOST_CHECK_EQUAL(cb2_called, true);
}

// Waits delay_ms milliseconds and then fires f with the given value.
void FireFutureAfterDelay(string value, int delay_ms, Future<string> f) {
  boost::this_thread::sleep(boost::posix_time::milliseconds(delay_ms));
  f.Fire(value);
}

// Check that Value() waits if necessary before returning the value.
BOOST_AUTO_TEST_CASE(ValueWait) {
  const char kFireValue[] = "Future Fired!";
  Future<string> f;
  boost::thread t(&FireFutureAfterDelay, kFireValue, 100, f);
  BOOST_CHECK_EQUAL(f.Value(), kFireValue);

  t.join();
}
