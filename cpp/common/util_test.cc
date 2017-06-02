//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for util.h 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   omd            Original Version
//*****************************************************************

#include "util.h"

#include <algorithm>
#include <boost/assign/list_of.hpp>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <memory>
#include <random>
#include <vector>

#define BOOST_TEST_MODULE UtilTest

#include "safe-file-stream.h"
#include "test-init.h"

using namespace std;

BOOST_AUTO_TEST_CASE(FileHandleOStreamWorks) {
  char tempfile[] = "/tmp/unit_test_XXXXXX";
  int fd = mkstemp(tempfile);
  FileHandleOStream output_stream(fd);

  output_stream << "Line 1\n" << "Line 2\n";
  output_stream.close();

  SafeIFStream instream(tempfile);
  string line;
  getline(instream, line);
  BOOST_CHECK_EQUAL(line, "Line 1");
  getline(instream, line);
  BOOST_CHECK_EQUAL(line, "Line 2");

  getline(instream, line);
  BOOST_CHECK_EQUAL(line.size(), 0);
  BOOST_CHECK_EQUAL(instream.eof(), true);
}

BOOST_AUTO_TEST_CASE(SpawnWorks) {
  // Spawn 'wc' and write some data to it. Make sure the output is as expected.
  auto_ptr<FileHandleOStream> process_stdin;
  auto_ptr<FileHandleIStream> process_stdout;
  vector<string> args;
  SpawnAndConnectPipes("/usr/bin/wc", args, &process_stdin, &process_stdout);

  *process_stdin << "Line 1\nLine 2\n";
  process_stdin->close();

  string output;
  getline(*process_stdout, output);
  BOOST_CHECK_EQUAL(output, "      2       4      14");
}

// Check that RandomSubset runs and returns the expected number of
// unique elements.
BOOST_AUTO_TEST_CASE(RandomSubsetBasicFunctionality) {
  vector<int> source;
  for (int i = 100; i < 207; ++i) {
    source.push_back(i);
  }

  std::set<int> results;
  int seed = std::chrono::system_clock::to_time_t(
      std::chrono::system_clock::now());
  LOG(INFO) << "Seed for this test: " << seed;
  mt19937 rng(seed);

  const int kSubsetSize = 20;
  RandomSubset(kSubsetSize, source.begin(), source.end(), &rng,
               inserter(results, results.begin()));
  BOOST_CHECK_EQUAL(results.size(), kSubsetSize);
}


// Check that RandomSubset works with a variety of container types
// and data types.
BOOST_AUTO_TEST_CASE(RandomSubsetIsGeneric) {
  int seed = std::chrono::system_clock::to_time_t(
      std::chrono::system_clock::now());
  LOG(INFO) << "Seed for this test: " << seed;
  mt19937 rng(seed);

  // Generate a vector of strings from which we'll randomly select.
  vector<string> src_strings_vec = boost::assign::list_of("One")("Two")("Three")
      ("Four")("Five");
  // And output the results into a vector
  vector<string> vec_str_results;

  RandomSubset(3, src_strings_vec.begin(), src_strings_vec.end(),
               &rng, back_inserter(vec_str_results));
  BOOST_CHECK_EQUAL(vec_str_results.size(), 3);
  for (auto v : vec_str_results) {
    BOOST_CHECK_MESSAGE(
        find(src_strings_vec.begin(), src_strings_vec.end(), v) !=
          src_strings_vec.end(),
        "Unable to find " << v << " in the set of source strings");
  }

  // Output the results into a standard C++ array
  string c_array_str_results[3];
  RandomSubset(3, src_strings_vec.begin(), src_strings_vec.end(),
               &rng, c_array_str_results);
  for (int j = 0; j < 3; ++j) {
    string v = c_array_str_results[j];
    BOOST_CHECK_MESSAGE(
        find(src_strings_vec.begin(), src_strings_vec.end(), v) !=
          src_strings_vec.end(),
        "Unable to find " << v << " in the set of source strings");
  }

  // Make the source a deque
  deque<string> src_strings_deq = boost::assign::list_of("One")("Two")("Three")
      ("Four")("Five");
  // And the destination a set
  set<string> set_str_results;
  RandomSubset(
      4, src_strings_deq.begin(), src_strings_deq.end(),
      &rng, inserter(set_str_results, set_str_results.begin()));
  BOOST_CHECK_EQUAL(set_str_results.size(), 4);

  // And make the source a vector<char> and the destination a set<char>
  vector<char> src_char_vec = boost::assign::list_of('a')('b')('c');
  set<char> set_char_results;
  RandomSubset(2, src_char_vec.begin(), src_char_vec.end(), &rng,
               inserter(set_char_results, set_char_results.begin()));
  BOOST_CHECK_EQUAL(set_char_results.size(), 2);
  // Even though a set holds unique elements and we checked that we had 2 of
  // them above, it can't hurt to double-check that we've got only values 'a',
  // 'b', or 'c'
  for (auto v : set_char_results) {
    BOOST_CHECK_MESSAGE(
        find(src_char_vec.begin(), src_char_vec.end(), v) !=
          src_char_vec.end(),
        "Unable to find " << v << " in the set of source strings");
  }
}

// Make sure all values in the orignal set are equally probable. We do this by
// generate 1000 random values. If things are equally probable the number of
// times we observe each value should have a binomial distribution. Thus, if
// there are 5 different values the probablity of seeing fewer than 142
// observations of any value is less than 1 in 1 million so we check that.
//
// Note: It's not actually a binomial distribution if we're drawing more than 1
// at a time since we're drawing without replacement. However, I don't know the
// right distribution and this should be awfully close.
BOOST_AUTO_TEST_CASE(RandomSubsetDistributionCorrect) {
  int seed = std::chrono::system_clock::to_time_t(
      std::chrono::system_clock::now());
  LOG(INFO) << "Seed for this test: " << seed;
  mt19937 rng(seed);

  vector<int> src;
  for (int i = 0; i < 5; ++i) {
    src.push_back(i);
  }

  // We try a few different subset sizes. Note that we need to make sure that
  // the subset size divides evenly into 1000.
  vector<int> subset_sizes = boost::assign::list_of(1)(2)(4)(5);

  for (int num_vals_per_subset : subset_sizes) {
    map<int, int> observations;
    for (int i = 0; i < 5; ++i) {
      observations[i] = 0;
    }
    const int kNumValues = 1000;

    int num_iters = kNumValues / num_vals_per_subset;
    for (int iter = 0; iter < num_iters; ++iter) {
      set<int> results;
      RandomSubset(num_vals_per_subset, src.begin(), src.end(), &rng,
                   inserter(results, results.begin()));
      for (auto v : results) {
        observations[v] += 1;
      }
    }

    int total_obs = 0;
    for (auto o : observations) {
      BOOST_CHECK_GE(o.second, 142);
      total_obs += o.second;
    }
    BOOST_CHECK_EQUAL(total_obs, kNumValues);
  }
}
