//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A test script that asks the client to perform a set of
//                     queries read from a file. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_QUERY_LIST_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_QUERY_LIST_SCRIPT_H_

#include <iostream>
#include <vector>
#include <boost/function.hpp>

#include "test-harness/common/test-script.h"
#include "common/knot.h"

class QueryCommand;
class GeneralLogger;

class QueryListScript : public TestScript {
 public:
  typedef boost::function<int ()> DelayFunction;

  /// Asks the client to run each of the queries in query_list_file
  /// num_iterations times (will go through the entire file once before
  /// repeating. The query_list_file is read in it's entirely in the constructor
  /// and the pointer need not be valid once the constructor has returned. This
  /// does not take ownership of the pointer.
  QueryListScript(std::istream* query_list_file,
                  int num_iterations,
                  DelayFunction delay_function,
                  QueryCommand* query_command,
                  GeneralLogger* logger);

  virtual ~QueryListScript() {}

  virtual void Run() = 0;

 /// Generally a better idea to have these be private and have accessors, but I
 /// think there's only going to be 2 subclasses and they're so similar that it
 /// seems like a waste of effort...
 protected:
  std::vector<Knot> queries_;
  std::vector<uint64_t> query_ids_;
  int num_iterations_;
  DelayFunction delay_function_;
  QueryCommand* query_command_;
  GeneralLogger* logger_;
};

#endif
