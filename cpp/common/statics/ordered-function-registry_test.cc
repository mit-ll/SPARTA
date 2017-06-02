//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for OrderedFunctionRegistry 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 May 2012   omd            Original Version
//*****************************************************************


#define BOOST_TEST_MODULE OrderedFunctionRegistryTest
#define BOOST_TEST_DYN_LINK

#include "ordered-function-registry.h"

// Note we can't use "init-test.h" here as that uses the statics stuff and this
// uses the statics stuff and...
#include <boost/test/unit_test.hpp>
#include <boost/bind.hpp>
#include <string>
#include <vector>

using std::string;
using std::vector;

// The following function will be wrapped with boost::bind so it has a void ()
// signature and can be called via OrderedFunctionRegistry. It just pushed the
// value on the vector. That way we can check the order that the functions we
// actually called.
void PushToVector(const string& value, vector<string>* dest) {
  dest->push_back(value);
}

BOOST_AUTO_TEST_CASE(OrderedFunctionRegistryWorks) {
  OrderedFunctionRegistry registry;
  vector<string> calls;
  // Add dependencies and functions in haphazard order as static initialization
  // is ill-defined.
  registry.AddFunction("F A", boost::bind(&PushToVector, "F A", &calls));
  registry.OrderConstraint("F A", "F B");
  registry.OrderConstraint("F A", "F C");
  registry.AddFunction("F B", boost::bind(&PushToVector, "F B", &calls));
  registry.OrderConstraint("F B", "F C");
  registry.AddFunction("F C", boost::bind(&PushToVector, "F C", &calls));

  registry.RunFunctions();

  BOOST_REQUIRE_EQUAL(calls.size(), 3);
  BOOST_CHECK_EQUAL(calls[0], "F A");
  BOOST_CHECK_EQUAL(calls[1], "F B");
  BOOST_CHECK_EQUAL(calls[2], "F C");
}
