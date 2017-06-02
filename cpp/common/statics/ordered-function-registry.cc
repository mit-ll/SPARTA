//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of OrderedFunctionRegistry 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 May 2012   omd            Original Version
//*****************************************************************

#include "ordered-function-registry.h"
#include "common/topological-iterator.h"
// Can't use CHECK as logging is intializied via OrderedFunctionRegistry!
#include <cassert>

using std::string;
using std::map;
using std::list;
using std::pair;

void OrderedFunctionRegistry::OrderConstraint(const string& before,
                                              const string& after) {
  // We have no way to know if before or after have already been registered as
  // statics are not initialized in any deterministic order (which is exactly
  // the problem this class is supposed to solve) so we just store the string
  // and check for existence when we get to RunFunctions().
  function_order_constraints_.push_back(make_pair(before, after));
}

void OrderedFunctionRegistry::RunFunctions() {
  TopologicalIterator<NamedFunction> function_ordering;
  map<string, VoidFunction>::iterator i;
  for (i = functions_to_run_.begin(); i != functions_to_run_.end(); ++i) {
    function_ordering.Add(*i);
  }

  list<pair<string, string> >::iterator j;
  for (j = function_order_constraints_.begin();
       j != function_order_constraints_.end(); ++j) {
    assert(functions_to_run_.find(j->first) != functions_to_run_.end());
    assert(functions_to_run_.find(j->second) != functions_to_run_.end());

    function_ordering.OrderConstraint(*functions_to_run_.find(j->first),
                                      *functions_to_run_.find(j->second));
  }

  // Now the ordering is set up so iterate through the functions in topological
  // order and run them.
  while(function_ordering.HasNext()) {
    function_ordering.Next().function_();
  }
}
