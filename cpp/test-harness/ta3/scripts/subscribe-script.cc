//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of SubscribeScript
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "subscribe-script.h"

#include <fstream>

#include "test-harness/ta3/multi-client-sut-protocol-stack.h"
#include "test-harness/ta3/client-sut-protocol-stack.h"
#include "test-harness/ta3/commands/subscribe-command.h"
#include "test-harness/common/delay-generators.h"
#include "common/general-logger.h"
#include "common/line-raw-data.h"

using namespace std;

SubscribeScript::SubscribeScript(
    LineRawData<Knot> command_data,
    MultiClientSUTProtocolStack* protocol_stack, 
    GeneralLogger* logger)
    : protocol_stack_(protocol_stack), logger_(logger) {
  ParseSubscribeSequence(command_data);
}

SubscribeScript::~SubscribeScript() {
  for (auto item : commands_) {
    delete item;
  }
  for (auto item : sut_ids_) {
    delete item;
  }
}

void SubscribeScript::ParseSubscribeSequence(LineRawData<Knot> command_data) {
  for (size_t i = 0; i < command_data.Size(); i++) {
    string line = command_data.Get(i).ToString();
    size_t space1 = line.find_first_of(' ', 0);
    size_t space2 = line.find_first_of(' ', space1 + 1);
    int sut_id = SafeAtoi(line.substr(0, space1));
    sut_ids_.push_back(new size_t(sut_id));
    string* sub_id = new string(line.substr(space1 + 1, space2 - space1 - 1));
    SafeAtoi(*sub_id);
    string* command_str = new string(line.substr(space2 + 1, string::npos));
    LineRawData<Knot>* command = new LineRawData<Knot>;
    command->AddLine(Knot(sub_id));
    command->AddLine(Knot(command_str));
    commands_.push_back(command);
  }
}

void SubscribeScript::Run() {
  LOG(INFO) << "SubscribeScript creating "
      << commands_.size() << " subscriptions";
  for (size_t i = 0; i < commands_.size(); ++i) {
    LOG(INFO) << "Creating subscription for client SUT " << *sut_ids_[i];

    // Will wait for the subscribe command to complete
    LogSubscribeCommandStatus(i, *sut_ids_[i], "STARTED");
    ClientSUTProtocolStack* client_ps =
      protocol_stack_->GetProtocolStack(*sut_ids_[i]);
    SubscribeCommand* subscribe_command = 
      client_ps->GetSubscribeCommand();
    NumberedCommandSender::ResultsFuture f = 
      subscribe_command->Schedule(*commands_[i], logger_);
    f.Wait();
    LogSubscribeCommandStatus(i, *sut_ids_[i], "FINISHED");
  }

  LOG(INFO) << "All subscriptions commands completed";
  logger_->Flush();
}

void SubscribeScript::LogSubscribeCommandStatus(
    size_t command_id, size_t sut_id, const char* state) {
  std::ostringstream out;
  out << "SubscribeScript command #" << command_id << 
         " to SUT " << sut_id << " " << state;
  logger_->Log(out.str());
}

////////////////////////////////////////////////////////////////////////////////
// SubscribeScriptFactory
////////////////////////////////////////////////////////////////////////////////

SubscribeScriptFactory::SubscribeScriptFactory(
    MultiClientSUTProtocolStack* protocol_stack, GeneralLogger* logger)
    : protocol_stack_(protocol_stack), logger_(logger) {
}

TestScript* SubscribeScriptFactory::operator()(
    const LineRawData<Knot>& command_data) {
  CHECK(command_data.Size() >= 1);

  return new SubscribeScript(
      command_data, 
      protocol_stack_, logger_);
}
