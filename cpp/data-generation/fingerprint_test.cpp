//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            yang
// Description:        Unit tests for FingerprintGenerator.cpp
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 June 2012  yang           Original Version
//*****************************************************************

#define BOOST_TEST_MODULE FingerprintGeneratorTest

#include <cstdlib>
#include <vector>
#include <cmath>

#include "fingerprint-generator.h"
#include "../common/test-init.h"
#include "../common/logging.h"

using namespace std;

// This test repetitively computes a sample mean and sample
// variance from a known underlying distribution, and tests
// whether they are consistent with the expected sample
// mean and expected sample variance.
//
// The expected sample mean and variance are computed analytically
// based on the underlying normal distribution and the effects of
// the flooring, which occurs in the implementation of GetRandomBits
// to ensure that the method returns a whole number of 32-bit integers.
BOOST_AUTO_TEST_CASE(VectorDistributionTest) {

  // Underlying distribution constants. These define the characteristics
  // of the normal distribution used to determine bit stream size.
  const int kMean = 10000;
  const int kStd = 688;
  const int kNumRows = 100;
  const int kVar = pow(kStd, 2);
  
  // A sigma value that characterizes the interval in which we deem the
  // difference between sample mean/variance and expected sample mean/variance
  // acceptable.
  //
  // Default set to 2 sigma. If GetRandomBits is correct, the sample mean
  // and variance will be captured within the 2-sigma confidence interval
  // 97.7% of the time.
  //
  // This value is arbitrarily set and there is no reason to change it.
  // It does not change the statistical power of the unit test.
  const int kToleranceSigma = 2;
  const float kZScore = 0.9772;
  // Number of times we compute the sampling mean and variance. Increasing
  // this will increase statistical power of the test.
  const unsigned int kNumTrials = 500;

  FingerprintGenerator generator(kMean, kStd);

  unsigned int seed = static_cast<unsigned int>(time(0));
  LOG(INFO) << "Seed: " << seed;

  generator.SetSeed(seed);

  int num_success_mean = 0;
  int num_success_var = 0;

  for (unsigned int n = 0; n < kNumTrials; ++n) {
    vector<int> rand_bits;
    long sum_size = 0;
    vector<int> sizes;
    sizes.reserve(kNumRows);
    for (int i = 0; i < kNumRows; ++i) {
      rand_bits.clear();
      generator.GetRandomBits(&rand_bits);
      sum_size += rand_bits.size() * sizeof(int);
      sizes.push_back(rand_bits.size() * sizeof(int));
    }
    float sample_mean = sum_size / (float) kNumRows;

    long sum_diff_from_mean = 0;
    for (int j = 0; j < kNumRows; ++j) {
      sum_diff_from_mean += pow(sizes[j] - sample_mean, 2);
    }
    float sample_var = sum_diff_from_mean / (float) kNumRows;
    sizes.clear();    
 
    // The sample mean is itself a random variable. The expected value is
    // kMean-2 and variance is approximately kStd^2/N. The expected value and
    // variance is not exactly kMean and kStd^2/N, respectively, because our
    // implmentation of FingerprintGenerator::GetRandomBits undershoots the
    // target size by 2 bytes due to 32-bit rounding.
    // 
    // We check to see that the sample mean and variance are reasonable based
    // on what we know about the underlying distribution.
    float expected_mean = kMean - 2.0;
    float expected_err_mean = kToleranceSigma * pow(kVar/ (float) kNumRows, 0.5);

    if (abs(sample_mean - expected_mean) <= expected_err_mean) {
      ++num_success_mean;
    }

    // The sample variance is also itself a random variable. Its expected value
    // is kVar and variance is approx. kVar^2 * (2/(N-1)) assuming no excess
    // kurtosis.
    float expected_var = (kNumRows-1) / (float) kNumRows * kVar;
    float expected_err_var = kToleranceSigma * pow(kVar,2) 
          * (2/(float)(kNumRows-1));

    if (abs(sample_var - expected_var) <= expected_err_var) {
      ++num_success_var;
    }
  }

  BOOST_CHECK_CLOSE(num_success_mean, kZScore * kNumTrials, 5);
  BOOST_CHECK_CLOSE(num_success_var, kZScore * kNumTrials, 5);
}

// Just checking that my new method doesn't crash. Not really doing any
// correctness checking.
// TODO(yang) njhwang: this unit test fails sometimes
BOOST_AUTO_TEST_CASE(TempHackTest) {
  const int kMean = 100;
  const int kStd = 2;
  FingerprintGenerator generator(kMean, kStd);

  unsigned int seed = static_cast<unsigned int>(time(0));
  LOG(INFO) << "Seed: " << seed;
  generator.SetSeed(seed);

  int length;
  char* result = generator.GetRandomBits(&length);
  BOOST_CHECK_GT(length, 0);
  free(result);
}
