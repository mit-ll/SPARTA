//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        All unit tests should #include this to initialize any
//                     statics, etc. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 May 2012   omd            Original Version
//*****************************************************************

/// This initializes statics, #include boost's unit test stuff and #defines the
/// right macro, before boost unit test #inclusion, to have the test dynamically
/// linked against the boost unit test runner and it's main() function.

#ifndef CPP_COMMON_TEST_INIT_H_
#define CPP_COMMON_TEST_INIT_H_

#include "statics.h"

#define BOOST_TEST_DYN_LINK
#include <boost/test/unit_test.hpp>

/// Perform simple initialization
class InitTest {
 public:
   InitTest() { Initialize(); }
  ~InitTest() {}
};

BOOST_GLOBAL_FIXTURE(InitTest);

#endif
