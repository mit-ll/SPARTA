//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for EquiProbableClosedSetField 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Jan 2013   omd            Original Version
//*****************************************************************


#define BOOST_TEST_MODULE EquiProbableClosedSetFieldTest
#include "common/test-init.h"

#include "equi-probable-closed-set-field.h"

#include <boost/assign/list_of.hpp>
#include <chrono>
#include <map>
#include <set>
#include <sstream>

#include "common/logging.h"

using namespace std;

// Very simple test to ensure that I can construct a EquiProbableClosedSetField
// and have the getter methods return the right stuff.
BOOST_AUTO_TEST_CASE(ConstructionWorks) {
  istringstream values_file(
      "V1\n"
      "V2\n"
      "Long Value 3\n"
      "value 4\n");

  EquiProbableClosedSetField epcsf("my field", &values_file);

  BOOST_CHECK_EQUAL(epcsf.name(), "my field");
  // 12 is the length of the longest value ("Long Value 3")
  BOOST_CHECK_EQUAL(epcsf.MaxLength(), 12);
}

// Generate 1k random values from a set of 5 possible ones. If the values are,
// in fact equally probably then we should see a roughly equal distribution of
// values. However, to make the test robust we provide bounds so that the
// probability of false failure is less that 1/1 million. Specifically, each
// RandomValue call is a Bernoulli trial so the number of successes in 1000
// trials is Binomially distributed. On average it would be 1000/5 == 200 for
// each value, but it should be less than 142 less than 1 in 1 million times.
// Note that there's no need to test the greater-than value as the sum of all 5
// observations must be 1,000.
BOOST_AUTO_TEST_CASE(RandomValueWorks) {
  const int kNumTrials = 1000;

  vector<string> values = boost::assign::list_of("value 1")
      ("SecondValue")("Third")("V4")("Val 5");
  stringstream values_file;
  map<string, int> observed_counts;
  for (auto v : values) {
    values_file << v << "\n";
    observed_counts[v] = 0;
  }


  EquiProbableClosedSetField fld("my field", &values_file);
  int seed = std::chrono::system_clock::to_time_t(
      std::chrono::system_clock::now());
  LOG(INFO) << "Seed for this test: " << seed;
  fld.SetSeed(seed);

  size_t buffer_size = fld.MaxLength();
  char buffer[buffer_size];

  for (int i = 0; i < kNumTrials; ++i) {
    char* result_end = fld.RandomValue(buffer_size, buffer); 
    BOOST_CHECK_LE(result_end, buffer + buffer_size);
    string result_str(buffer, result_end - buffer);
    BOOST_CHECK_MESSAGE(
        observed_counts.find(result_str) != observed_counts.end(),
        "Unexpected value returned by RandomValue: " << result_str);
    observed_counts[result_str] += 1;
  }

  int total_count = 0;
  for (auto val_cnt_pair : observed_counts) {
    // See comments above to see where 142 comes from.
    BOOST_CHECK_MESSAGE(
        val_cnt_pair.second >= 142,
        "Only observed " << val_cnt_pair.second << " values "
        "for " << val_cnt_pair.first);
    total_count += val_cnt_pair.second;
  }
  // This shouldn't be necessary - it's just a sanity check.
  BOOST_CHECK_EQUAL(total_count, kNumTrials);
}


// Very much like the test above, but there are 7 total values and we call
// RandomValueExcluding and exlude two of them (thus having only 5 values that
// should be generated which is the same as the above so all the calculations
// about bounds still hold).
BOOST_AUTO_TEST_CASE(RandomValueExcludingWorks) {
  const int kNumTrials = 1000;

  vector<string> values = boost::assign::list_of("value 1")
      ("SecondValue")("Third")("V4")("Val 5");
  BOOST_CHECK_EQUAL(values.size(), 5);

  set<string> excluded = boost::assign::list_of("exluded 1")
      ("excluded number 2");
  BOOST_CHECK_EQUAL(excluded.size(), 2);

  stringstream values_file;
  map<string, int> observed_counts;
  for (auto v : values) {
    values_file << v << "\n";
    observed_counts[v] = 0;
  }

  // Add the exculded values to the set that are valid to the field, but don't
  // add them to observed_counts so the check that every generated value is
  // already in the observed_counts map also checks that we didn't generate
  // anything we should be excluding.
  for (auto v : excluded) {
    values_file << v << "\n";
  }

  EquiProbableClosedSetField fld("my field", &values_file);
  int seed = std::chrono::system_clock::to_time_t(
      std::chrono::system_clock::now());
  LOG(INFO) << "Seed for this test: " << seed;
  fld.SetSeed(seed);

  size_t buffer_size = fld.MaxLength();
  char buffer[buffer_size];

  for (int i = 0; i < kNumTrials; ++i) {
    char* result_end = fld.RandomValueExcluding(excluded, buffer_size, buffer); 
    BOOST_CHECK_LE(result_end, buffer + buffer_size);
    string result_str(buffer, result_end - buffer);
    BOOST_CHECK_MESSAGE(
        observed_counts.find(result_str) != observed_counts.end(),
        "Unexpected value returned by RandomValue: " << result_str);
    observed_counts[result_str] += 1;
  }

  int total_count = 0;
  for (auto val_cnt_pair : observed_counts) {
    // See comments above to see where 142 comes from.
    BOOST_CHECK_MESSAGE(
        val_cnt_pair.second >= 142,
        "Only observed " << val_cnt_pair.second << " values "
        "for " << val_cnt_pair.first);
    total_count += val_cnt_pair.second;
  }
  // This shouldn't be necessary - it's just a sanity check.
  BOOST_CHECK_EQUAL(total_count, kNumTrials);
}
