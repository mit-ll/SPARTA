//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A test harness script that executes one modify command
//                     after another, waiting for each to complete before
//                     running the next one. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_UNLOADED_MODIFY_ARGUMENT_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_UNLOADED_MODIFY_ARGUMENT_SCRIPT_H_

#include "modify-argument-script.h"

class UnloadedModifyArgumentScript : public ModifyArgumentScript {
 public:
  /// This expects command_data to contain a RUNSCRIPT line followed by a series
  /// of modify commands as per ModifyArgumentScript. It will exeucte each
  /// command, waiting for any pending command to complete before running the
  /// next one.
  UnloadedModifyArgumentScript(
      InsertCommand* insert_command, UpdateCommand* update_command,
      DeleteCommand* delete_command, GeneralLogger* logger,
      const LineRawData<Knot>& command_data);

  virtual ~UnloadedModifyArgumentScript() {}

  virtual void Run();
};

/// Functor for use with ScriptManager so one of these can be constructed.
class UnloadedModifyArgumentFactory {
 public:
  UnloadedModifyArgumentFactory(
      InsertCommand* insert_command, UpdateCommand* update_command,
      DeleteCommand* delete_command, GeneralLogger* logger)
      : insert_command_(insert_command), update_command_(update_command),
        delete_command_(delete_command), logger_(logger) {
  }

  TestScript* operator()(const LineRawData<Knot>& command_data) {
    return new UnloadedModifyArgumentScript(
        insert_command_, update_command_, delete_command_, logger_,
        command_data);
  }

 private:
  InsertCommand* insert_command_;
  UpdateCommand* update_command_;
  DeleteCommand* delete_command_;
  GeneralLogger* logger_;
};


#endif
