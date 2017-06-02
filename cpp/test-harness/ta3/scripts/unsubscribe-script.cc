//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of UnsubscribeScript
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "unsubscribe-script.h"

#include <fstream>

#include "test-harness/ta3/multi-client-sut-protocol-stack.h"
#include "test-harness/ta3/client-sut-protocol-stack.h"
#include "test-harness/ta3/commands/unsubscribe-command.h"
#include "test-harness/common/delay-generators.h"
#include "common/general-logger.h"
#include "common/line-raw-data.h"

using namespace std;

UnsubscribeScript::UnsubscribeScript(
    LineRawData<Knot> command_data,
    MultiClientSUTProtocolStack* protocol_stack, 
    GeneralLogger* logger)
    : protocol_stack_(protocol_stack), logger_(logger) {
  ParseUnsubscribeSequence(command_data);
}

UnsubscribeScript::~UnsubscribeScript() {
  for (auto item : commands_) {
    delete item;
  }
  for (auto item : sut_ids_) {
    delete item;
  }
}

void UnsubscribeScript::ParseUnsubscribeSequence(LineRawData<Knot> command_data) {
  for (size_t i = 0; i < command_data.Size(); i++) {
    string line = command_data.Get(i).ToString();
    size_t space1 = line.find_first_of(' ', 0);
    int sut_id = SafeAtoi(line.substr(0, space1));
    sut_ids_.push_back(new size_t(sut_id));
    string* sub_id = new string(line.substr(space1 + 1, string::npos));
    SafeAtoi(*sub_id);
    LineRawData<Knot>* command = new LineRawData<Knot>;
    command->AddLine(Knot(sub_id));
    commands_.push_back(command);
  }
}

void UnsubscribeScript::Run() {
  LOG(INFO) << "UnsubscribeScript performing "
      << commands_.size() << " unsubscriptions";
  for (size_t i = 0; i < commands_.size(); ++i) {
    LOG(INFO) << "Performing unsubscription for client SUT " << *sut_ids_[i];

    // Will wait for the unsubscribe command to complete
    LogUnsubscribeCommandStatus(i, *sut_ids_[i], "STARTED");
    ClientSUTProtocolStack* client_ps =
      protocol_stack_->GetProtocolStack(*sut_ids_[i]);
    UnsubscribeCommand* unsubscribe_command = 
      client_ps->GetUnsubscribeCommand();
    NumberedCommandSender::ResultsFuture f = 
      unsubscribe_command->Schedule(*commands_[i], logger_);
    f.Wait();
    LogUnsubscribeCommandStatus(i, *sut_ids_[i], "FINISHED");
  }

  LOG(INFO) << "All unsubscription commands completed";
  logger_->Flush();
}

void UnsubscribeScript::LogUnsubscribeCommandStatus(
    size_t command_id, size_t sut_id, const char* state) {
  std::ostringstream out;
  out << "UnsubscribeScript command #" << command_id << 
         " to SUT " << sut_id << " " << state;
  logger_->Log(out.str());
}

////////////////////////////////////////////////////////////////////////////////
// UnsubscribeScriptFactory
////////////////////////////////////////////////////////////////////////////////

UnsubscribeScriptFactory::UnsubscribeScriptFactory(
    MultiClientSUTProtocolStack* protocol_stack, GeneralLogger* logger)
    : protocol_stack_(protocol_stack), logger_(logger) {
}

TestScript* UnsubscribeScriptFactory::operator()(
    const LineRawData<Knot>& command_data) {
  CHECK(command_data.Size() >= 1);

  return new UnsubscribeScript(
      command_data, 
      protocol_stack_, logger_);
}
