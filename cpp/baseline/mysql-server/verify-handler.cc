//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************

#include "verify-handler.h"

#include <functional>

#include "common/string-algo.h"

void VerifyHandler::Execute(LineRawData<Knot>* command_data) {
  // Event ID 11: Verify command received
  if (events_enabled_) {
    WriteEvent(11);
  }
  connection_pool_->AddWork(
      std::bind(&VerifyHandler::DoVerify, this, std::placeholders::_1,
                command_data));
}

void VerifyHandler::DoVerify(MySQLConnection* connection,
                             LineRawData<Knot>* command_data) {
  // Event ID 12: Verify processing began
  if (events_enabled_) {
    WriteEvent(12);
  }
  // Don't forget to free it
  std::unique_ptr<LineRawData<Knot> > command_data_ptr(command_data);

  CHECK(command_data->Size() == 1);

  Knot verify_cmd_str = command_data->Get(0);
  CHECK(verify_cmd_str.StartsWith("VERIFY "));

  Knot::iterator row_id_start = verify_cmd_str.IteratorForChar(
      strlen("VERIFY ")); 

  const std::string row_id = verify_cmd_str.SubKnot(
      row_id_start, verify_cmd_str.end()).ToString();

  std::string query("SELECT * FROM main WHERE id = ");
  query += row_id;

  // Event ID 13: Verify command submitted
  if (events_enabled_) {
    WriteEvent(13);
  }
  int result = mysql_real_query(connection->GetConnection(),
                                query.data(), query.size());
  if (result != 0) {
    LOG(FATAL) << "Error running VERIFY command:\n"
        << mysql_error(connection->GetConnection());
  }

  int num_rows_returned = 0;
  MYSQL_RES* result_set = mysql_store_result(connection->GetConnection());
  CHECK(result_set != NULL)
      << "Error retrieving data for verify command:\n"
      << mysql_error(connection->GetConnection());

  for (MYSQL_ROW row = mysql_fetch_row(result_set);
       row != nullptr; row = mysql_fetch_row(result_set)) {
    ++num_rows_returned;
  }
  mysql_free_result(result_set);

  if (num_rows_returned == 1) {
    WriteResults("DONE\n");
  } else {
    LineRawData<Knot> err_msg;
    err_msg.AddLine(Knot(new std::string("FAILED")));
    std::string* false_str = new std::string("VERIFY FALSE");
    err_msg.AddLine(Knot(false_str));
    std::string* reason_str = new std::string("Record ");
    *reason_str += row_id;
    if (num_rows_returned == 0) {
      *reason_str += " could not be found";
    } else {
      *reason_str += " found ";
      *reason_str += itoa(num_rows_returned);
      *reason_str += " times";
    }
    err_msg.AddLine(Knot(reason_str));
    err_msg.AddLine(Knot(new std::string("ENDFAILED")));
    
    WriteResults(err_msg);
  }
  Done();
}
