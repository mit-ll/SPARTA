//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for FutureWaiter. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE FutureWaiterTest
#include "test-init.h"

#include "future-waiter.h"

#include <functional>
#include <chrono>
#include <thread>
#include <vector>

#include "future.h"

using namespace std;

// We'll spawn this function in a separate thread. It will wait on all the
// passed futures and set all_done to true when they have all fired. The main
// test then makes sure that boolean gets set at the right time.
void WaitingFunction(vector<Future<bool> >* futures,
                     bool* all_done) {
  BOOST_CHECK_EQUAL(*all_done, false);
  FutureWaiter<bool> waiter;
  for (vector<Future<bool> >::iterator i = futures->begin();
       i != futures->end(); ++i) {
    waiter.Add(*i);
  }

  waiter.Wait();
  *all_done = true;
}


BOOST_AUTO_TEST_CASE(FutureWaiterWorks) {
  vector<Future<bool> > futures;
  for (int i = 0; i < 100; ++i) {
    futures.push_back(Future<bool>());
  }

  bool all_futures_fired = false;
  std::thread waiting_thread(
      std::bind(&WaitingFunction, &futures, &all_futures_fired));

  BOOST_CHECK_EQUAL(all_futures_fired, false);

  // Fire the 1st 50 futures
  size_t i;
  for (i = 0; i < 50; ++i) {
    futures[i].Fire(true);
  }
  BOOST_CHECK_EQUAL(all_futures_fired, false);

  // Now wait a little while to make sure the thread doesn't unlock
  // prematurely.
  std::this_thread::sleep_for(std::chrono::milliseconds(100));
  BOOST_CHECK_EQUAL(all_futures_fired, false);

  // Fire the final set of futures, wait for the thread to join, and then
  // everything should be fired.
  for (; i < futures.size(); ++i) {
    futures[i].Fire(true);
  }

  waiting_thread.join();
  BOOST_CHECK_EQUAL(all_futures_fired, true);
}
