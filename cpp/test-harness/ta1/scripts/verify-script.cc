//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of VerifyScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
//*****************************************************************

#include "verify-script.h"

#include <algorithm>
#include <cstring>

#include "common/check.h"
#include "test-harness/ta1/verify-command.h"

VerifyScript::VerifyScript(LineRawData<Knot>* row_id, 
                           LineRawData<Knot>* mod_id,
                           VerifyCommand* verify_command,
                           GeneralLogger* logger)
    : row_id_(row_id), mod_id_(mod_id), verify_command_(verify_command),
      logger_(logger) {
  CHECK(row_id->Size() == 1);
  CHECK(mod_id->Size() == 1);
}

void VerifyScript::Run() {
  std::string desc_message("MID ");
  desc_message += mod_id_->Get(0).ToString();
  desc_message += ": VERIFY ";
  desc_message += row_id_->Get(0).ToString();
  NumberedCommandSender::ResultsFuture f =
      verify_command_->Schedule(*row_id_, logger_, -1, desc_message);
  f.Wait();
  logger_->Flush();
}

////////////////////////////////////////////////////////////////////////////////
// VerifyScriptFactory
////////////////////////////////////////////////////////////////////////////////

TestScript* VerifyScriptFactory::operator()(
    const LineRawData<Knot>& command_data) {
  CHECK(command_data.Size() == 2)
      << "Expected only two arguments to VerifyScriptFactory, received "
      << command_data.Size() << ".\nFirst argument: " << command_data.Get(0);
  Knot mod_id_knot = command_data.Get(0);
  Knot row_id_knot = command_data.Get(1);
  DCHECK(std::all_of(mod_id_knot.begin(), mod_id_knot.end(),
                     [] (char x) { return isdigit(x); }));
  DCHECK(std::all_of(row_id_knot.begin(), row_id_knot.end(),
                     [] (char x) { return isdigit(x); }));

  LineRawData<Knot>* row_id = new LineRawData<Knot>;
  row_id->AddLine(row_id_knot);
  LineRawData<Knot>* mod_id = new LineRawData<Knot>;
  mod_id->AddLine(mod_id_knot);

  return new VerifyScript(row_id, mod_id, verify_command_, logger_);
}
