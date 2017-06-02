//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class that builds INSERT statements for the keyword and
//                     stemming index tables. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_MYSQL_SERVER_INDEX_TABLE_INSERT_BUILDER_H_
#define CPP_BASELINE_MYSQL_SERVER_INDEX_TABLE_INSERT_BUILDER_H_

#include <set>
#include <string>
#include <vector>

#include "common/knot.h"
#include "notes-parser.h"

/// This class takes the data in a notes-like field and builds insert statements
/// for the keyword and stemming index tables. The returned statements are simple
/// strings. I decided not to use prepared statements for this because prepared
/// statements don't support the syntax where you have multiple rows in the
/// VALUES clause and I assume lots of round-trips will be slower than a single
/// statement that inserts 10's or 100's of rows. This choice also makes it much
/// easier to unit test as no MySQL connection objects are required.
class IndexTableInsertBuilder {
 public:
  /// Constructs a builder that will construct statements for the keyword and
  /// stem index tables with the given names.
  IndexTableInsertBuilder(
      const std::string& keyword_index_name,
      const std::string& stem_index_name,
      const std::set<std::string>& stop_words);
  virtual ~IndexTableInsertBuilder() {}

  /// Constructs a keyword index and stem index insert statement for the given
  /// row id and field. The statements are returned in keyword_statement and
  /// stem_statement respectively.
  void GetInsertStatements(
      const std::string& row_id, const std::string& field_name,
      const Knot& data, std::string* keyword_statement,
      std::string* stem_statement) const;

 private:
  std::string GetSingleStatement(
      const std::string& index_table, const std::string& row_id,
      const std::string& column,
      const std::set<std::string>& items) const;

  std::string keyword_index_name_;
  std::string stem_index_name_;
  NotesParser parser_;
};

#endif
