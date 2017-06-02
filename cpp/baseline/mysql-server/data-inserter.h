//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Class for handling the insertion of data into MySQL. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 03 Oct 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_BASELINE_MYSQL_SERVER_DATA_INSERTER_H_
#define CPP_BASELINE_MYSQL_SERVER_DATA_INSERTER_H_

#include <mysql/mysql.h>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <map>
#include <set>

#include "baseline/common/mysql-connection.h"
#include "common/line-raw-data.h"
#include "common/knot.h"
#include "index-table-insert-builder.h"
#include "bind-manager.h"
#include "alarm-words.h"

class MySQLConnection;
class Schema;

/// This class takes care of inserting data into all the necessary MySQL tables.
/// This includes the tables that form the main view as well as the index tables
/// that make keyword search and stemming searches possible.
///
/// This is a separate class, rather than a NumberedCommandHandler as this will
/// be used both in a command handler and in the initial data ingestion (either
/// called from Python or with data piped from the Python data generator).
class DataInserter {
 public:
  /// Inserts data using the given connection (takes ownership of the
  /// connection). The schema, set of fields to be indexed for keyword and
  /// stemming, and a set of stop words are also provided. This does *not* take
  /// ownership of those items.
  DataInserter(std::auto_ptr<MySQLConnection> connection,
               const Schema* schema,
               const std::set<std::string>& stop_words);
  virtual ~DataInserter();

  /// Given LineRawData containing one value per field in the schema this inserts
  /// the data into all the necessary tables. This takes ownership of data and
  /// frees it after the insert is complete. Calls the given DoneCallback (if
  /// specified) when the insertion is complete. Also optionally takes in an
  /// EventCallback that can be called when reportable events occur.
  typedef std::function<void ()> DoneCallback;
  typedef std::function<void (int, std::string*)> EventCallback;
  void PerformInserts(LineRawData<Knot>* data, 
                      LineRawData<Knot>* hash = nullptr,
                      DoneCallback cb = nullptr,
                      EventCallback eb = nullptr);

 private:
  /// Creates MySQL prepared statements for all the tables. Prepared statements
  /// should be much faster than building an SQL string. Clearly this saves the
  /// server parsing time, but more importantly it allows us to send binary data,
  /// like the fingerprint field, as binary data without having to escape it,
  /// copy it to a different char*, etc.
  void PrepareStatements();
  void PrepareStatement(const std::string& table_name, 
                        const std::vector<std::string>& field_names);
  /// Prepare the bind data structures.
  void PrepareStatementBinds(const std::string& table_name);

  std::auto_ptr<MySQLConnection> connection_;
  const Schema* schema_;

  IndexTableInsertBuilder index_insert_builder_;
  AlarmWords alarm_words_;

  /// Map from table name to a MySQL prepared statement for inserting into that
  /// table.
  std::map<std::string, MYSQL_STMT*> prep_stmt_map_;
  /// Map from table name to MYSQL_BIND structures for the insert statements for
  /// that table. There is one BindManager in bind_manager_map_ for each of
  /// these.
  std::map<std::string, MYSQL_BIND*> bind_map_;
  /// Map from field (table, field) to the BindManager that can do the MySQL
  /// prepared statement binding for that field.
  std::map<std::pair<std::string, std::string>, BindManager*> bind_manager_map_;
};

#endif
