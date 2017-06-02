//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of UpdateHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Oct 2012   omd            Original Version
//*****************************************************************

#include "update-handler.h"

#include <functional>
#include <sstream>
#include <vector>
#include <memory>
#include <map>

#include "baseline/common/common-mysql-defs.h"
#include "common/schema.h"

using namespace std;

UpdateHandler::UpdateHandler(
    ObjectThreads<MySQLConnection>* connection_pool,
    Schema* schema, 
    const std::set<std::string>& stop_words,
    bool events_enabled)
    : schema_(schema), 
      events_enabled_(events_enabled),
      connection_pool_(connection_pool),
      index_insert_builder_(kKeywordIndexTableName, kStemsIndexTableName,
                            stop_words) {
}

void UpdateHandler::Execute(LineRawData<Knot>* command_data) {
  CHECK(command_data->Size() > 2);
  // Event ID 8: Update command received
  if (events_enabled_) {
    WriteEvent(8);
  }
  Knot update_cmd_str = command_data->Get(0);
  CHECK(update_cmd_str.StartsWith("UPDATE "));
  CHECK(command_data->Get(command_data->Size() - 1) == "ENDUPDATE");
  const int row_id_offset = strlen("UPDATE ");

  Knot::iterator row_id_start = update_cmd_str.IteratorForChar(row_id_offset);
  string row_id = update_cmd_str.SubKnot(
      row_id_start, update_cmd_str.end()).ToString();

  command_data->SetStartOffset(1);
  command_data->SetEndOffset(1);
 
  connection_pool_->AddWork(
     std::bind(&UpdateHandler::DoUpdate, this, std::placeholders::_1,
               row_id, command_data)); 
}

void UpdateHandler::DoUpdate(MySQLConnection* connection, const string row_id,
                             LineRawData<Knot>* command_data) {
  // Event ID 9: Update processing began
  if (events_enabled_) {
    WriteEvent(9);
  }
  // Ensure the data gets freed. Note that since this is called via bind it'd be
  // difficult to have the acutal paramter be a unique_ptr.
  std::unique_ptr<LineRawData<Knot> > command_data_ptr(command_data);

  CHECK(command_data->Size() % 2 == 0)
      << "Update command should contain alternating column name, value pairs.";

  vector<string> statements = GetSQLStatements(row_id,
                                               command_data, connection);

  for (const string& statement : statements) {
    // Event ID 10: Update command submitted
    if (events_enabled_) {
      WriteEvent(10);
    }
    int res = mysql_real_query(connection->GetConnection(),
                               statement.data(), statement.size());
    if (res != 0) {
      LOG(FATAL) << "Error running update statement:\n"
          << mysql_error(connection->GetConnection());
    }
  }

  WriteResults("DONE\n");
  Done();
}

// TODO(odain) The focus here is on simple, maintainable code. This could almost
// certianly be faster, but since the test doesn't involve many updates and
// since this isn't a core part of the BAA I didn't try to optimize this.
//
// We need to determine several things here:
//
// 1) Which fields in which tables need to be updated
// 2) Which indexes need to be updated (which involves deleting the old data and
//    inserting new data).
std::vector<std::string> UpdateHandler::GetSQLStatements(
   const std::string& row_id, LineRawData<Knot>* command_data,
   MySQLConnection* mysql_connection) const {
  // Map from table name to update statements for that table.
  map<string, ostringstream* > table_update_map;
  // vector of all table sql statements. These are somewhat order dependent
  // (e.g. the deletes must happen before the inserts) so we will initially put
  // just index delete/insert statements here and then add the UPDATE statements
  // after that.
  vector<string> all_sql_stmts;
  // We have to lock all the tables we plan to update so we don't violate the
  // atomicity constraints. Note that you can only access tables that you have
  // locked so we have to lock everything we'll need here. We could try to be
  // smart and only lock those tables we'll need, but I'm inclined to be dumb
  // here as it's easier and this isn't time critical ;)
  ostringstream lock_tables_stmt;
  if (schema_->RequiresIndex()) {
    lock_tables_stmt << "LOCK TABLES " << kKeywordIndexTableName << " WRITE, "
        << kStemsIndexTableName << " WRITE";
    for (auto& table_to_lock : schema_->GetAllTables()) {
      lock_tables_stmt << ", " << table_to_lock << " WRITE";
    }
    all_sql_stmts.push_back(lock_tables_stmt.str());
  }

  size_t cmd_data_idx = 0;
  while (cmd_data_idx < command_data->Size()) {
    string column = command_data->Get(cmd_data_idx).ToString();
    // We've already checked that Size() % 2 == 0 so this should be unnecessary.
    DCHECK((cmd_data_idx + 1) < command_data->Size());
    Knot value = command_data->Get(cmd_data_idx + 1);
    cmd_data_idx += 2;

    const vector<FieldId>* field_ids = schema_->GetFieldIdsForField(column);
    for (FieldId fid : *field_ids) {
      auto update_stmt_iter = table_update_map.find(fid.table());

      FieldInfo f_info = schema_->GetFieldInfo(fid);
      string value_str = GetSQLString(mysql_connection, value, f_info);
      DCHECK(value_str.size() > 0);
      
      if (update_stmt_iter == table_update_map.end()) {
        ostringstream* statement_stream = new ostringstream;
        *statement_stream << "UPDATE " << fid.table() << " SET "
            << column << " = " << std::move(value_str);
        table_update_map[fid.table()] = statement_stream;
      } else {
        ostringstream* statement_stream = update_stmt_iter->second;
        *statement_stream << ", " << column << " = " << std::move(value_str);
      }

      if (schema_->GetFieldInfo(fid).index) {
        DCHECK(schema_->RequiresIndex());
        all_sql_stmts.push_back(
            string("DELETE FROM ") + kKeywordIndexTableName +
            " WHERE id = " + row_id + " and col = '" + fid.field() + "'");
        all_sql_stmts.push_back(
            string("DELETE FROM ") + kStemsIndexTableName +
            " WHERE id = " + row_id + " and col = '" + fid.field() + "'");
        string keyword_stmt, stem_stmt;
        index_insert_builder_.GetInsertStatements(
            row_id, fid.field(), value, &keyword_stmt, &stem_stmt);
        all_sql_stmts.push_back(keyword_stmt);
        all_sql_stmts.push_back(stem_stmt);
      }
    }
  }

  for (pair<string, ostringstream*> statement_streams : table_update_map) {
    *statement_streams.second << " where id = " << row_id;
    all_sql_stmts.push_back(statement_streams.second->str());
    delete statement_streams.second;
  }

  if (schema_->RequiresIndex()) {
    all_sql_stmts.push_back("UNLOCK TABLES");
  }

  return all_sql_stmts;
}

std::string UpdateHandler::GetSQLString(
       MySQLConnection* connection, Knot data, const FieldInfo& f_info) const {
  string result_str;
  if (schema_->RequiresEscaping(f_info)) {
    char* result = new char[data.Size() * 2 + 1];
    string to_escape;
    data.ToString(&to_escape);
    size_t result_size = mysql_real_escape_string(
        connection->GetConnection(), result, to_escape.data(),
        to_escape.size());
    DCHECK(schema_->RequiresQuotes(f_info));
    result_str.reserve(result_size + 2);
    result_str = "'";
    result_str += result;
    result_str += "'";
    delete[] result;
  } else {
    if (schema_->RequiresQuotes(f_info)) {
      result_str.reserve(data.Size() + 2);
      result_str = "'" + data.ToString() + "'";
    } else {
      data.ToString(&result_str);
    }
  }
  return result_str;
}
