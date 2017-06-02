//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for the Stem function 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Oct 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE StemmerTest
#include "common/test-init.h"

#include "stemmer.h"

#include <set>
#include <string>

using namespace std;

// helper method for making debug messages.
string GetSetContents(const set<string>& inputs) {
  string output;
  for (set<string>::const_iterator i = inputs.begin();
       i != inputs.end(); ++i) {
    if (!output.empty()) {
      output += ", ";
    }
    output += "'" + *i + "'";
  }
  return output;
}

BOOST_AUTO_TEST_CASE(StemmerWorks) {
  set<string> inputs;
  set<string> expected_outputs;

  // The follow examples come from the paper on the Porter algorithm.
  inputs.insert("relational");
  expected_outputs.insert("relat");

  inputs.insert("hopping");
  expected_outputs.insert("hop");

  inputs.insert("conditionally");
  expected_outputs.insert("condition");

  set<string> results;
  Stem(inputs, &results);

  for (set<string>::const_iterator i = expected_outputs.begin();
       i != expected_outputs.end(); ++i) {
    BOOST_CHECK_MESSAGE(results.find(*i) != results.end(),
                        "'" << *i << "' not found in the result set. "
                        << "Results contain:\n" << GetSetContents(results));
  }
}
