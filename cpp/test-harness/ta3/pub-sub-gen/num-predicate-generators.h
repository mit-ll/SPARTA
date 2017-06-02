//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A collection of generators for use with
//                     LowMatchRatePubSubGen. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Jan 2013   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA3_PUB_SUB_GEN_NUM_PREDICATE_GENERATORS_H_
#define CPP_TEST_HARNESS_TA3_PUB_SUB_GEN_NUM_PREDICATE_GENERATORS_H_

#include <random>

class NumGenerator {
  public:
    NumGenerator() {};
    virtual int operator()(int max) = 0;
    virtual int operator()() = 0;
};

/// Generates a "truncated" Poisson distribution with the given mean. The
/// truncation occurs on both the low end and the high end of the distribution.
/// The low-end occurs because we don't want to return 0, and the high end occurs
/// because we can't return a value > the number of avaialable fields.
/// Trunacation happens by rounding up or down to the closest legal value (as
/// opposed to discarding the value and generating a new one.).
class TruncatedPoissonNumGenerator : public NumGenerator {
 public:
  /// Will generate numbers with the given mean. The random number generator is
  /// seeded with seed.
  TruncatedPoissonNumGenerator(int mean, int seed);
  int operator()(int max);
  int operator()();

 private:
  std::mt19937 rng_;
  std::poisson_distribution<> dist_;
};

/// Constant number generator
class ConstantNumGenerator : public NumGenerator {
 public:
  ConstantNumGenerator(int value);
  int operator()(int max);
  int operator()();

 private:
  int value_;
};

/// Coin toss number generator
class CoinTossNumGenerator : public NumGenerator {
 public:
  CoinTossNumGenerator(int heads, int tails, float prob, int seed);
  int operator()(int max);
  int operator()();

 private:
  std::mt19937 rng_;
  std::uniform_real_distribution<float> dist_;
  int heads_;
  int tails_;
  float prob_;
};

#endif
