//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for AggregatingFuture
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Nov 2012   omd            Original Version
//*****************************************************************


#define BOOST_TEST_MODULE AggregatingFutureTest
#include "test-init.h"

#include <boost/thread.hpp>
#include <boost/bind.hpp>
#include <string>

#include "aggregating-future.h"
#include "check.h"
#include "conditions.h"
#include "string-algo.h"

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

// Simple test aggregator that keeps a running sum of all the partial results.
// When Finalize is called it converts the sum to a string and returns that.
class IntegerSumToString : public FutureAggregator<string, int> {
 public:
  IntegerSumToString() : sum_(0) {}
  virtual ~IntegerSumToString() {}

  virtual void AddPartialResult(const int& partial_result) {
    sum_ += partial_result;
  }

 protected:
  virtual string Finalize() {
    return itoa(sum_);
  }

 private:
  int sum_;
};

BOOST_AUTO_TEST_CASE(AggregationWorks) {
  IntegerSumToString agg;
  Future<string> f = agg.GetFuture();

  agg.AddPartialResult(10);
  agg.AddPartialResult(2);
  agg.AddPartialResult(8);
  agg.AddPartialResult(2);

  agg.Done();

  BOOST_CHECK_EQUAL(f.Value(), "22");
}

// A little bit of everything! Here we use a Future in aggregating mode. We set
// a callback, and we have another thread waiting on the Future to fire. We
// check that the callback and the waiting thread receive the expected data.
BOOST_AUTO_TEST_CASE(AggregationWaitAndCallbackWork) {
  IntegerSumToString agg;
  Future<string> f = agg.GetFuture();

  agg.AddPartialResult(10);

  bool wait_finished = false;
  SimpleCondition<bool> thread_waiting(false);
  boost::thread t(&WaitAndExpect<string>, f, &thread_waiting,
                  "100", &wait_finished);

  bool cb1_called = false;
  f.AddCallback(
      boost::bind(&CheckExpectedCallback<string>, "100", _1, &cb1_called));

  agg.AddPartialResult(80);
  agg.AddPartialResult(10);

  // Make sure the thread is running and waiting on this future.
  thread_waiting.Wait(true);

  agg.Done();

  BOOST_CHECK_EQUAL(cb1_called, true);
  t.join();
  BOOST_CHECK_EQUAL(wait_finished, true);

  // Add another callback. Since the Future already fired this should be called
  // immediately.
  bool cb2_called = false;
  f.AddCallback(
      boost::bind(&CheckExpectedCallback<string>, "100", _1, &cb2_called));
  BOOST_CHECK_EQUAL(cb2_called, true);
}
