//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A NumberedCommandHandler for database queries. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 May 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_MYSQL_CLIENT_QUERY_HANDLER_H_
#define CPP_MYSQL_CLIENT_QUERY_HANDLER_H_

/// Note that regex is part of the C++11 standard but it is not yet implemented
/// in g++. However, the boost libraries are TR1 and should be compatible with
/// the standard.
#include <boost/regex.hpp>
#include <iostream>
#include <string>

#include "baseline/common/numbered-command-receiver.h"
#include "baseline/common/mysql-connection.h"
#include "common/object_threads.h"

/// NumberedCommandHandler that executes the query its given. As currently
/// written it expects commands to be exactly one line that starts with "SELECT"
/// in all caps (as per the test plan).
class QueryHandler : public NumberedCommandHandler {
 public:
  /// Constructor. connection_pool is the thread pool on which operations will be
  /// scheduled. This does not take ownership of the pool. If query_log is not
  /// NULL all queries sent to the server will be logged to this stream. The time
  /// for the query to complete will also be logged. This does not take ownership
  /// of query_log. events_enabled indicates whether this QueryHandler should
  /// report event messages during query handling.
  /// Also takes in the maximum number of times a query will be submitted before
  /// being considered a failure, and whether event message reporting should be
  /// enabled.
  QueryHandler(ObjectThreads<MySQLConnection>* connection_pool,
               std::ostream* query_log, 
               int max_retries,
               bool events_enabled = false);
  virtual ~QueryHandler() {}

  /// Called by the base class when there's a query to execute.
  virtual void Execute(LineRawData<Knot>* command);

 protected:
  /// Checks to see if the query contains CONTAINED_IN or CONTAINS_STEM calls.
  /// This is actually a bit tricky as those are valid strings inside quotes and
  /// such. Note that this assumes (as is guaranteed by the test plan) that these
  /// calls will be in capital letters.
  bool NeedsExpansion(const std::string& query) const;

  void ExpandQuery(std::string* query) const;

 private:
  /// Execute simply schedules RunQuery to run on the 1st available thread in the
  /// connection_pool_.
  void RunQuery(MySQLConnection* connection, LineRawData<Knot>* command_data);
  /// Given the connection after a query has been executed this retrieves all the
  /// results from the server and writes the results via GetLROHandler().
  void ProcessResults(MySQLConnection* connection);

  /// Copy of the connection_pool pointer passed to the constructor.
  ObjectThreads<MySQLConnection>* connection_pool_;
  /// Pointer to query log output.
  std::ostream* query_log_;
  /// Maximum number of times a query will be resubmitted before being considered
  /// a failure.
  int max_retries_;
  /// Whether event message reporting is enabled.
  bool events_enabled_;

  /// The regular expression we use to check for the existence of CONTAINED_IN
  /// and CONTAINS_STEM calls. We initialize it in the constructor so that we
  /// only pay that cost once.
  static boost::regex* expand_funs_regex_;
  /// The regular expression we use to break apart a SELECT statement.
  static boost::regex* select_stmt_regex_;
  /// And regular expressions to break apart CONTAINED_IN, CONTAINS_STEM,
  /// and WORD_PROXIMITY calls.
  static boost::regex* contained_in_regex_;
  static boost::regex* contains_stem_regex_;
  static boost::regex* id_replace_regex_;
  static boost::regex* word_prox_regex_;
  static boost::regex* prox_ranking_regex_;
  static boost::regex* xml_value_regex_;
  friend void InitializeQueryHandlerRegex();
  friend void FreeQueryHandlerRegex();
};

#endif
