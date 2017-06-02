//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A handler for DELETE commands. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 30 Oct 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_BASELINE_MYSQL_SERVER_DELETE_HANDLER_H_
#define CPP_BASELINE_MYSQL_SERVER_DELETE_HANDLER_H_

#include "baseline/common/numbered-command-receiver.h"
#include "baseline/common/mysql-connection.h"
#include "common/object_threads.h"

class Schema;

class DeleteHandler : public NumberedCommandHandler {
 public:
  DeleteHandler(ObjectThreads<MySQLConnection>* connection_pool, 
                Schema* schema, 
                bool events_enabled = false);

  virtual void Execute(LineRawData<Knot>* command_data);
 private:
  void DoDelete(MySQLConnection* connection, LineRawData<Knot>* command_data);

  ObjectThreads<MySQLConnection>* connection_pool_;
  Schema* schema_;
  bool events_enabled_;
};

#endif
