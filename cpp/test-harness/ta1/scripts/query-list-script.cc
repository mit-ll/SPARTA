//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of QueryListScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************

#include "query-list-script.h"

#include <string>

#include "test-harness/common/delay-generators.h"

using std::vector;
using std::string;

QueryListScript::QueryListScript(
    std::istream* query_list_file, int num_iterations,
    QueryListScript::DelayFunction delay_function,
    QueryCommand* query_command, GeneralLogger* logger)
    : num_iterations_(num_iterations), delay_function_(delay_function),
      query_command_(query_command), logger_(logger) {
  // Read the entire list of queries into memory so timing isn't affected by
  // disk I/O.
  while (query_list_file->good()) {
    string *query = new string;
    getline(*query_list_file, *query);
    if (!query->empty()) {
      Knot query_knot(query);
      Knot query_id_knot = query_knot.Split(query_knot.Find('S'));
      LOG(DEBUG) << "Parsing query id: " << query_id_knot;
      LOG(DEBUG) << "Converting query id to: " 
                 << ConvertString<uint64_t>(query_id_knot.ToString());
      CHECK(query_knot.StartsWith("SELECT")) << "Invalid query specification: " 
                                             << *query;
      query_knot.AppendOwned("\n", 1);
      queries_.push_back(query_knot);
      query_ids_.push_back(ConvertString<uint64_t>(query_id_knot.ToString()));
    } else {
      delete query;
    }
  }

  CHECK(query_list_file->eof())
      << "Reading list of queries failed.";
}
