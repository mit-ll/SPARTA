//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for FieldSet 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Jan 2013   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE FieldSetTest
#include "common/test-init.h"

#include "field-set.h"

#include <chrono>
#include <set>
#include <sstream>
#include <string>

#include "common/string-algo.h"
#include "equi-probable-closed-set-field.h"
#include "testing-field-set.h"

using namespace std;

BOOST_AUTO_TEST_CASE(AppendFromFileWorks) {
  TestingFieldSet fs;
  istringstream fields_file(
      "fname EQFakeFactory Oliver Nick Mayank Ben\n"
      "# This is a comment. It's followed by a blank\n"
      "\n"
      "state EQFakeFactory OR MA\n");
  fs.AppendFromFile(&fields_file);

  int seed = std::chrono::system_clock::to_time_t(
      std::chrono::system_clock::now());
  LOG(INFO) << "Seed for this test: " << seed;
  fs.SetSeed(seed);

  BOOST_REQUIRE_EQUAL(fs.Size(), 2);
  const FieldBase* f1 = fs.Get(0);
  BOOST_CHECK_EQUAL(f1->NumValues(), 4);

  // Generate 1000 random values. With *very* probability (well more than
  // 999,999 times in a million) all 4 names will be produced. Make sure they're
  // the 4 values we provided.
  set<string> generated;
  const int buffer_size = f1->MaxLength();
  // The longest names are Oliver and Mayank, both of which are 6 characters.
  BOOST_CHECK_EQUAL(buffer_size, 6);
  char buffer[buffer_size];
  for (int i = 0; i < 1000; ++i) {
     char* val_end = f1->RandomValue(buffer_size, buffer);
     generated.insert(string(buffer, val_end));
  }

  BOOST_CHECK(generated.find("Oliver") != generated.end());
  BOOST_CHECK(generated.find("Nick") != generated.end());
  BOOST_CHECK(generated.find("Mayank") != generated.end());
  BOOST_CHECK(generated.find("Ben") != generated.end());

  // And do the same checks for the other field.
  const FieldBase* f2 = fs.Get(1);
  BOOST_CHECK_EQUAL(f2->NumValues(), 2);

  // This is smaller than the 6 characters we allocated for buffer above so
  // we're OK
  BOOST_REQUIRE_EQUAL(f2->MaxLength(), 2);

  generated.clear();
  for (int i = 0; i < 1000; ++i) {
     char* val_end = f2->RandomValue(buffer_size, buffer);
     generated.insert(string(buffer, val_end));
  }

  BOOST_CHECK(generated.find("MA") != generated.end());
  BOOST_CHECK(generated.find("OR") != generated.end());
}
