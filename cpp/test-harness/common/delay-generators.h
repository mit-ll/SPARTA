//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Handy functions for use with VariableDelayQueryScript and
//                     VariableDelayModifyScript. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_DELAY_GENERATORS_H_
#define CPP_TEST_HARNESS_COMMON_DELAY_GENERATORS_H_

#include <boost/random/exponential_distribution.hpp>
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/uniform_real.hpp>
#include <boost/random/variate_generator.hpp>

const int kNumMillisecondsPerSecond = 1000;
const int kNumMicroSecondsPerMillisecond = 1000;
const int kNumMicroSecondsPerSecond =
    kNumMicroSecondsPerMillisecond * kNumMillisecondsPerSecond;

/// A function that always returns 0. This allows us to test maximum throughput.
inline int ZeroDelay() {
  return 0;
}

class FixedDelayFunctor {
 public:
  FixedDelayFunctor(int microseconds) : microseconds_(microseconds) {}

  FixedDelayFunctor(const FixedDelayFunctor& other)
      : microseconds_(other.microseconds_) {}

  int operator()() {
    return microseconds_;
  }

 private:
  int microseconds_;
};

/// A functor that draws exponentially distributed values with the given mean.
/// Note that this must be constructed with a seed so that the results are
/// predictable even if different perfomers run a different number of scripts or
/// a different number of queries.
///
/// Note: This has to take the floor to return an int so it won't be terribley
/// accurate for time scales less than about 1 millisecond. Luckily, I don't
/// think we'll ever generate data on a time scale smaller than that.
class ExponentialDelayFunctor {
 public:
  /// mean_microseconds is the mean for the distribuiton in microseconds
  /// seed is the seed to use to initialize the RNG.
  ExponentialDelayFunctor(int mean_microseconds, int seed)
      : rng_(seed), mean_microseconds_(mean_microseconds),
        exp_gen_(rng_, boost::exponential_distribution<>(
                1.0 / float(mean_microseconds_))) {
  }

  /// Need an explicit copy constructor as the variate_generator keeps a
  /// reference to the rng_ inside it so it can't just be copied from another one
  /// of these.
  ExponentialDelayFunctor(const ExponentialDelayFunctor& other)
      : rng_(other.rng_), mean_microseconds_(other.mean_microseconds_),
        exp_gen_(rng_, boost::exponential_distribution<>(
                1.0 / float(mean_microseconds_))) {
  }

  int operator()() {
    float microseconds_f = exp_gen_();
    return floor(microseconds_f);
  }

 private:
  /// Mersenne Twister random number generator.
  boost::mt19937 rng_;
  /// This is only needed so we can copy-construct these.
  int mean_microseconds_;
  /// And a generator for exponentials.
  boost::variate_generator< boost::mt19937&,
      boost::exponential_distribution<> > exp_gen_;
};

#endif
