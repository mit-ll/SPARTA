//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************

#include "insert-atomicity-script.h"

#include <boost/bind.hpp>

#include "query-command.h"
#include "test-harness/common/th-run-script-command.h"
#include "common/general-logger.h"
#include "common/future-waiter.h"

InsertAtomicityScript::InsertAtomicityScript(
    const Knot& query, LineRawData<Knot>* insert_data,
    QueryCommand* query_command, THRunScriptCommand* run_script_command,
    GeneralLogger* logger)
    : TestScript(RUN_ONCE), query_(query), insert_data_(insert_data),
      query_command_(query_command), run_script_command_(run_script_command),
      logger_(logger) {
}

void InsertAtomicityScript::Run() {
  THRunScriptCommand::ResultsFuture f_started, f_done;

  run_script_command_->SendRunScript(*insert_data_, f_started, f_done);

  f_started.AddCallback(
      boost::bind(&InsertAtomicityScript::LogStarted, this));

  FutureWaiter<NumberedCommandSender::SharedResults> waiter;
  while (!f_done.HasFired()) {
    waiter.Add(query_command_->Schedule(query_, logger_));
  }

  logger_->Log("Insert command complete");
  waiter.Wait();
  logger_->Log("All pending queries complete");
}

void InsertAtomicityScript::LogStarted() {
  logger_->Log("Insert command started");
}
