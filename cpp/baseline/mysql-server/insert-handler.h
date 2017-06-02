//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A NumberedCommandHandler for database inserts. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 May 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_MYSQL_SERVER_INSERT_HANDLER_H_
#define CPP_MYSQL_SERVER_INSERT_HANDLER_H_

#include "baseline/common/numbered-command-receiver.h"
#include "common/object_threads.h"
#include "data-inserter.h"

#include <string>
#include <vector>
#include <map>

class Schema;

class InsertHandler : public NumberedCommandHandler {
 public:
  /// This does not take ownership of the insert_pool
  InsertHandler(ObjectThreads<DataInserter>* insert_pool,
                bool events_enabled = false)
      : insert_pool_(insert_pool), events_enabled_(events_enabled) {
  }
  virtual void Execute(LineRawData<Knot>* command_data);
 private:
  /// Called by DataInserter when the insert completes.
  void InsertDone();

  ObjectThreads<DataInserter>* insert_pool_;
  bool events_enabled_;
};

#endif
