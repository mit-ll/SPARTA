//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for things defined in
//                     variable-delay-query-script.h. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE DelayGeneratorsTest
#include "common/test-init.h"

#include "delay-generators.h"

#include <boost/function.hpp>
#include <ctime>
#include <memory>
#include <vector>

#include "common/logging.h"

using namespace std;

// Checks that the ExponentialDelayFunctor does indeed return numbers that are,
// in fact, exponentially distributed. The test works as follows:
//
// 1) We generate numbers with a mean of 3 milliseconds until we've seen a total
//    of ten seconds (e.g. the sum of the generated numbers > 10 seconds)
// 2) We count the number of events in the 10 second period.
// 3) If the data were really Poisson we should see, on average, 3,333 events.
// 4) Using a little R to help us (ppois and qpois specifically) we find that
//    the observed number of events will be less than 3062 only 1 in 1 million
//    times and it will be greater than 3611 only 1 in 1 million times.
// 5) Note that if we were generating with a mean of 4 instead of 3 the mean
//    number of observations would be 2500 which is well outside this range.
//    Similarly, if we generated with a mean of 2 instead of 3 the mean would be
//    5000 which is, again, outside this range. Thus, we have a very good chance
//    to catching errors even with this low probability of FA. 
BOOST_AUTO_TEST_CASE(ExponentialDelayFunctorDistributionCorrect) {
  int seed = time(NULL);
  LOG(DEBUG) << "Running with seed: " << seed;

  ExponentialDelayFunctor f(3 * kNumMicroSecondsPerMillisecond, seed);

  double total_time = 0;
  const int kNumMicrosInTenSeconds = 10 * kNumMicroSecondsPerSecond;
  int num_events = 0;
  while (true) {
    total_time += f();
    if (total_time > kNumMicrosInTenSeconds) {
      break;
    } else {
      ++num_events;
    }
  }

  // See comments
  BOOST_CHECK_LT(num_events, 3611);
  BOOST_CHECK_GT(num_events, 3062);
}

// Test that the generated numbers are the same if we generate them twice with
// the same seed.
BOOST_AUTO_TEST_CASE(ExponentialDelayFunctorStableSeed) {
  const int kSeed = 11098234;
  ExponentialDelayFunctor f1(10 * kNumMicroSecondsPerMillisecond, kSeed);

  // Probability of getting 10 identical values if they are different is
  // essentially 0.
  const int kNumValsToGenerate = 10;

  std::vector<int> f1_generated;
  for (int i = 0; i < kNumValsToGenerate; ++i) {
    f1_generated.push_back(f1());
  }

  ExponentialDelayFunctor f2(10 * kNumMicroSecondsPerMillisecond, kSeed);
  std::vector<int> f2_generated;
  for (int i = 0; i < kNumValsToGenerate; ++i) {
    f2_generated.push_back(f2());
  }

  for (int i = 0; i < kNumValsToGenerate; ++i) {
    BOOST_CHECK_EQUAL(f1_generated[i], f2_generated[i]);
  }


}

// We pass these functors by value. I was getting strange memory errors so this
// test checks that doing this is valid.
BOOST_AUTO_TEST_CASE(ExponentialDelayFunctorCopyable) {
  auto_ptr<ExponentialDelayFunctor> f1(
      new ExponentialDelayFunctor(10000, 1342));
  BOOST_CHECK_GE((*f1)(), 0);
  // Will eventually copy f2 into f3
  boost::function<int ()> f3;

  {
    boost::function<int ()> f2 = *f1;
    BOOST_CHECK_GE(f2(), 0);

    f3 = f2;
    BOOST_CHECK_GE(f3(), 0);

    f1.reset();
    BOOST_CHECK_GE(f2(), 0);
    BOOST_CHECK_GE(f3(), 0);
  }
  // Now f2 is out of scope, but f3 should still be callable.
  BOOST_CHECK_GE(f3(), 0);
}
