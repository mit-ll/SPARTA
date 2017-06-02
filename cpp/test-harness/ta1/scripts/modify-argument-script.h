//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Base class for scripts that accept modify commands via
//                     the network. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_MODIFY_ARGUMENT_SCRIPT_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_MODIFY_ARGUMENT_SCRIPT_H_

#include <vector>

#include "test-harness/common/test-script.h"
#include "common/check.h"

class GenericNumberedCommand;
class DeleteCommand;
class InsertCommand;
class UpdateCommand;
class GeneralLogger;

/// This class defines a base class for test scripts that get called over the
/// network from the test harness component driving the client. Subclasses
/// handle whatever arguments they expect in the received LineRawData and then
/// call ParseCommandData passing the index of the 1st line the case class
/// should parse. This class then parses out a set of commands which should
/// have the following form:
///
///  MODIFY_COMMAND_TYPE
///  <.data.>
///  ENDDATA
///
///  MODIFY_COMMAND_TYPE is one of INSERT, UPDATE, DELETE and the <.data.>
///  between the command type and ENDDATA gets passed through directly to the
///  appropriate command (e.g. InsertCommand, UpdateCommand, or DeleteCommand). 
///
/// Subclasses generally then call GetCommandData and GetCommandHandler to get
/// the data for the command and the insert, updat, or delete command that
/// should process that data.
class ModifyArgumentScript : public TestScript {
 public:
  ModifyArgumentScript(InsertCommand* insert_command,
                       UpdateCommand* update_command,
                       DeleteCommand* delete_command,
                       GeneralLogger* logger);

  virtual ~ModifyArgumentScript();

  virtual void Run() = 0;

 protected:
  InsertCommand* GetInsertCommand() {
    return insert_command_;
  }

  UpdateCommand* GetUpdateCommand() {
    return update_command_;
  }

  DeleteCommand* GetDeleteCommand() {
    return delete_command_;
  }

  GeneralLogger* GetLogger() {
    return logger_;
  }

  int NumCommands() const {
    DCHECK(command_handlers_.size() == commands_data_.size());
    return command_handlers_.size();
  }

  GenericNumberedCommand* GetCommandHandler(size_t i) {
    DCHECK(command_handlers_.size() > i);
    return command_handlers_[i];
  }

  LineRawData<Knot>* GetCommandData(size_t i) {
    DCHECK(commands_data_.size() > i);
    return commands_data_[i];
  }

  std::string GetCommandDescMessage(size_t i, 
				    const std::string& command_name) {
    std::string desc_message("MID ");
    desc_message += command_mod_ids_[i];
    desc_message += ": ";
    desc_message += command_name;
    desc_message += " ";
    desc_message += command_row_ids_[i]; 
    return desc_message;
  }

  /// Parse the command_data starting at commands_start_offset (the data before
  /// this is assumed to be data that's specific to the subclass.
  void ParseCommandData(
      int commands_start_offset, const LineRawData<Knot>& command_data);

  /// Parse the command_data starting at commands_start_offset the MID 
  /// should be the first line
  void ParseCommandModID(const LineRawData<Knot>& command_data);

  GeneralLogger* logger_;

 private:
  /// Called by ParseCommandData to send any additional data to the specific
  /// command. For example, ParseCommandData might recognize an INSERT command.
  /// It would then call this to send the LineRawData for that insert command to
  /// the command itself.
  void PopulateCommandsData(const LineRawData<Knot>& command_data, size_t* i);

  InsertCommand* insert_command_;
  UpdateCommand* update_command_;
  DeleteCommand* delete_command_;

  /// command_mod_ids_[i] is the modification ID for the command
  /// used for logging
  std::vector<std::string> command_mod_ids_;
  /// command_row_ids_[i] is the row ID the command is operating on
  /// used for logging
  std::vector<std::string> command_row_ids_;
  /// commands_data_[i] is the LineRawData that should be sent to the insert,
  /// update or delete command for execution.
  std::vector<LineRawData<Knot>*> commands_data_;
  /// command_handlers[i] is a pointer to an InsertCommand, UpdateCommand, or
  /// DeleteCommand; whatever is appropriate for handling commands_data[i].
  std::vector<GenericNumberedCommand*> command_handlers_;
};

#endif
