//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A handler for the VERIFY command 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_BASELINE_MYSQL_SERVER_VERIFY_HANDLER_H_
#define CPP_BASELINE_MYSQL_SERVER_VERIFY_HANDLER_H_

#include "baseline/common/numbered-command-receiver.h"
#include "baseline/common/mysql-connection.h"
#include "common/object_threads.h"

// TODO(njhwang) build unit tests for this
class VerifyHandler : public NumberedCommandHandler {
 public:
  VerifyHandler(ObjectThreads<MySQLConnection>* connection_pool,
                bool events_enabled = false)
      : connection_pool_(connection_pool), events_enabled_(events_enabled) {}
  virtual ~VerifyHandler() {}

  virtual void Execute(LineRawData<Knot>* command_data);
 private:
  void DoVerify(MySQLConnection* connection, LineRawData<Knot>* command_data);

  ObjectThreads<MySQLConnection>* connection_pool_;
  bool events_enabled_;
};

#endif
