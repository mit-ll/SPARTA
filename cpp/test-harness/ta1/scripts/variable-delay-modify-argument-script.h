//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A script that performs a series of modify commands
//                     received over the network with a variable amount of delay
//                     between each command. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_VARIABLE_DELAY_MODIFY_ARGUMENT_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_VARIABLE_DELAY_MODIFY_ARGUMENT_SCRIPT_H_

#include "modify-argument-script.h"

/// This script is used by the test harness controlling the server to perform a
/// series of database modifications with variable delay. The delay is controlled
/// by the parameters passed to the constructor.
class VariableDelayModifyArgumentScript : public ModifyArgumentScript {
 public:
  /// This expects command_data to start with  the following lines:
  ///
  /// - The name of the delay function to use (either NO_DELAY or
  ///   EXPONENTIAL_DELAY)
  /// - If the delay function is EXPONENTIAL_DELAY this is the mean delay in
  ///   microseconds. Otherwise this line is absent.
  /// - The rest of the lines contain the modify commands to send as per
  ///   ModifyArgumentScript.
  VariableDelayModifyArgumentScript(
      InsertCommand* insert_command, UpdateCommand* update_command,
      DeleteCommand* delete_command, GeneralLogger* logger,
      const LineRawData<Knot>& command_data);

  virtual ~VariableDelayModifyArgumentScript() {}

  virtual void Run();

 private:
  typedef boost::function<int ()> DelayFunction;

  DelayFunction delay_function_;
};

/// Functor for use with ScriptManager so one of these can be constructed.
class VariableDelayModifyFactory {
 public:
  VariableDelayModifyFactory(
      InsertCommand* insert_command, UpdateCommand* update_command,
      DeleteCommand* delete_command, GeneralLogger* logger)
      : insert_command_(insert_command), update_command_(update_command),
        delete_command_(delete_command), logger_(logger) {
  }

  TestScript* operator()(const LineRawData<Knot>& command_data) {
    return new VariableDelayModifyArgumentScript(
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
