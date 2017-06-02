//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of DeleteHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 30 Oct 2012   omd            Original Version
//*****************************************************************

#include "delete-handler.h"

#include <functional>
#include <sstream>
#include <string>

#include "baseline/common/common-mysql-defs.h"
#include "common/schema.h"

DeleteHandler::DeleteHandler(ObjectThreads<MySQLConnection>* connection_pool, 
                             Schema* schema, 
                             bool events_enabled)
  : connection_pool_(connection_pool), 
    schema_(schema),
    events_enabled_(events_enabled) {
}

void DeleteHandler::Execute(LineRawData<Knot>* command_data) {
  CHECK(command_data->Size() == 1);
  // Event ID 0: Delete command received
  if (events_enabled_) {
    WriteEvent(0);
  }
  connection_pool_->AddWork(
      std::bind(&DeleteHandler::DoDelete, this, std::placeholders::_1,
                command_data));
}

void DeleteHandler::DoDelete(
    MySQLConnection* connection, LineRawData<Knot>* command_data) {
  // Event ID 1: Delete processing began
  if (events_enabled_) {
    WriteEvent(1);
  }
  // Make sure we free the memory when we're done with it.
  std::unique_ptr<LineRawData<Knot> > command_data_ptr(command_data);

  Knot delete_cmd_str = command_data->Get(0);
  CHECK(delete_cmd_str.StartsWith("DELETE "));

  Knot::iterator row_id_start = delete_cmd_str.IteratorForChar(
      strlen("DELETE ")); 

  const std::string row_id = delete_cmd_str.SubKnot(
      row_id_start, delete_cmd_str.end()).ToString();

  auto tables = schema_->GetAllTables();
  // Only process keywords and stems tables if indexing was required.
  if (schema_->RequiresIndex()) {
    tables.insert(kKeywordIndexTableName);
    tables.insert(kStemsIndexTableName);
  }

  for (auto& table : tables) {
    std::ostringstream query;
    query << "DELETE from " << table << " where id = " << row_id;

    std::string query_str = std::move(query.str());

    // Event ID 2: Delete command submitted
    if (events_enabled_) {
      WriteEvent(2);
    }

    int res = mysql_real_query(connection->GetConnection(),
                               query_str.data(), query_str.size());
    if (res != 0) {
      // TODO(odain) If we can determine that this query would succeed if
      // retried we should send WriteResults("FAILED")...
      LOG(FATAL) << "Error running delete statement:\n"
          << mysql_error(connection->GetConnection());
    }
  }

  WriteResults("DONE\n");
  Done();
}
