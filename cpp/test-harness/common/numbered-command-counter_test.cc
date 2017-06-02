//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for NumberedCommandCounter 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE NumberedCommandCounterTest
#include "common/test-init.h"

#include <algorithm>
#include <boost/bind.hpp>
#include <boost/thread.hpp>
#include <vector>

#include "numbered-command-counter.h"

using namespace std;

// See the IncrementingFromThreadsWorks test below...
void DoIncrementing(int num_to_generate, vector<int>* generated) {
  generated->reserve(num_to_generate);
  for (int i = 0; i < num_to_generate; ++i) {
    generated->push_back(NumberedCommandCounter::Increment());
  }
}

// Spawn a bunch of threads and have them all fill up vectors of counters as
// fast as they can. Then concatenate all the vectors together and sort them.
// The result should be a single list of values, starting at 0, with no gaps.
// Ensure that is in fact the case.
BOOST_AUTO_TEST_CASE(IncrementingFromThreadsWorks) {
  const int kNumTestThreads = 10;
  const int kNumNumbersPerThread = 1000;

  vector<boost::thread> threads;
  threads.reserve(kNumTestThreads);

  vector<vector<int> > generated_vectors(kNumTestThreads);

  for (int i = 0; i < kNumTestThreads; ++i) {
    threads.push_back(boost::thread(
            boost::bind(&DoIncrementing, kNumNumbersPerThread,
                        &generated_vectors[i])));
  }

  // Wait for all the threads to finish.
  for (auto& thread : threads) {
    thread.join();
  }

  // Now concatenate all the results.
  vector<int> results;
  results.reserve(kNumNumbersPerThread * kNumTestThreads);
  for (auto numbers : generated_vectors) {
    results.insert(results.end(), numbers.begin(), numbers.end());
  }

  // Sort all the generated data
  sort(results.begin(), results.end());

  // Finally, make sure we got one of every number.
  for (int i = 0; i < kNumTestThreads * kNumNumbersPerThread; ++i) {
    BOOST_CHECK_EQUAL(results[i], i);
  }
}
