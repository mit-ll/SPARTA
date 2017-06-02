//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A NumberedCommandHandler for database updates. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_BASELINE_MYSQL_SERVER_UPDATE_HANDLER_H_
#define CPP_BASELINE_MYSQL_SERVER_UPDATE_HANDLER_H_

#include <memory>
#include <string>
#include <set>

#include "baseline/common/numbered-command-receiver.h"
#include "baseline/common/mysql-connection.h"
#include "common/object_threads.h"
#include "index-table-insert-builder.h"

class FieldInfo;
class Schema;

class UpdateHandler : public NumberedCommandHandler {
 public:
  UpdateHandler(ObjectThreads<MySQLConnection>* connection_pool,
                Schema* schema, 
                const std::set<std::string>& stop_words,
                bool events_enabled = false);

  virtual void Execute(LineRawData<Knot>* command_data);

 protected:
  /// This is virtual and protected to facilitate unit testing. In order to
  /// escpae strings you need a MySQLConnection but we won't have that in unit
  /// tests. Thus, we'll have a unit test class that simply returns whatever
  /// data gets passed to it and you can test the GetSQLStatements method to
  /// ensure the SQL strings are correct. The "real" implementation will escape
  /// those items that need it (depending on f_info) and return the string
  /// (escaped or otherwise).
  virtual std::string GetSQLString(
      MySQLConnection* connection, Knot data, const FieldInfo& f_info) const;

  std::vector<std::string> GetSQLStatements(
      const std::string& row_id, LineRawData<Knot>* command_data,
      MySQLConnection* mysql_connection) const;

  Schema* schema_;
  bool events_enabled_;

 private:
  void DoUpdate(MySQLConnection* connection, const std::string row_id,
                LineRawData<Knot>* command_data);

  ObjectThreads<MySQLConnection>* connection_pool_;
  IndexTableInsertBuilder index_insert_builder_;
};

#endif
