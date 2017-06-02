//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************

#include "modify-argument-script.h"

#include "test-harness/ta1/insert-command.h"
#include "test-harness/ta1/update-command.h"
#include "test-harness/ta1/delete-command.h"

ModifyArgumentScript::ModifyArgumentScript(
    InsertCommand* insert_command, UpdateCommand* update_command,
    DeleteCommand* delete_command, GeneralLogger* logger)
    : logger_(logger), insert_command_(insert_command), 
      update_command_(update_command), delete_command_(delete_command) {}

ModifyArgumentScript::~ModifyArgumentScript() {
  std::vector<LineRawData<Knot>*>::iterator i;
  for (i = commands_data_.begin(); i != commands_data_.end(); ++i) {
    delete *i;
  }
}

void ModifyArgumentScript::ParseCommandModID(const LineRawData<Knot>& command_data) {

  int commands_start_offset = 0;
  DCHECK(static_cast<size_t>(commands_start_offset) < command_data.Size());
  CHECK(!command_data.IsRaw(commands_start_offset));
  Knot mod_id = command_data.Get(commands_start_offset);
  command_mod_ids_.push_back(mod_id.ToString());
}

void ModifyArgumentScript::ParseCommandData(
    int commands_start_offset, const LineRawData<Knot>& command_data) {
  DCHECK(commands_start_offset >= 0);
  DCHECK(static_cast<size_t>(commands_start_offset) < command_data.Size());
  size_t i = commands_start_offset;
  while (i < command_data.Size()) {
    CHECK(command_data.IsRaw(i) == false);
    if (command_data.Get(i) == "INSERT") {
      command_handlers_.push_back(insert_command_);
    } else if (command_data.Get(i) == "UPDATE") {
      command_handlers_.push_back(update_command_);
    } else {
      CHECK(command_data.Get(i) == "DELETE")
          << "Unknown modify command: " << command_data.Get(i);
      command_handlers_.push_back(delete_command_);
    }

    ++i;
    PopulateCommandsData(command_data, &i);
  }
}

void ModifyArgumentScript::PopulateCommandsData(
    const LineRawData<Knot>& command_data, size_t* i) {
  DCHECK(*i < command_data.Size());
  DCHECK(*i >= 0);
  LineRawData<Knot>* new_data = new LineRawData<Knot>;
  while (true) {
    if (command_data.IsRaw(*i)) {
      new_data->AddRaw(command_data.Get(*i));
    } else {
      if (command_data.Get(*i) == "ENDDATA") {
        *i += 1;
        break;
      } else {
       new_data->AddLine(command_data.Get(*i));
      }
    } 
    *i += 1;
    CHECK(*i < command_data.Size());
  }

  commands_data_.push_back(new_data);
  DCHECK(commands_data_.size() == command_handlers_.size());

  // Store the row id which is the first line in new_data
  DCHECK(0 < new_data->Size());
  Knot row_id = new_data->Get(0);
  command_row_ids_.push_back(row_id.ToString());
}

