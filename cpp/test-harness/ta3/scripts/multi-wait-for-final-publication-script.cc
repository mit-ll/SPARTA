//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implmentation of MultiWaitForFinalPublicationScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "multi-wait-for-final-publication-script.h"

#include "test-harness/ta3/multi-client-sut-protocol-stack.h"
#include "test-harness/ta3/client-sut-protocol-stack.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/sut-running-monitor.h"
#include "common/general-logger.h"
#include "common/event-loop.h"

using namespace std;

MultiWaitForFinalPublicationScript::MultiWaitForFinalPublicationScript(
    int timeout, MultiClientSUTProtocolStack* sut_protocols,
    GeneralLogger* logger)
    : timeout_(timeout), sut_protocols_(sut_protocols),
      logger_(logger) {
}

void MultiWaitForFinalPublicationScript::Run() {
  LOG(INFO) << "Instituting timeout for final publications on all client SUTs";
  vector<WaitForFinalPublicationScript*> wait_scripts;
  vector<Future<bool>> done_futures;
  for (size_t i = 0; i < sut_protocols_->GetNumClientSUTs(); i++) {
    ClientSUTProtocolStack* client_protocols = 
      sut_protocols_->GetProtocolStack(i);
    PublicationReceivedHandler* pub_handler =
      client_protocols->GetPublicationReceivedHandler();
    WaitForFinalPublicationScript* wait_script =
      new WaitForFinalPublicationScript(timeout_, pub_handler, logger_);
    wait_scripts.push_back(wait_script);
    done_futures.push_back(wait_script->RunInThread());
  }
  for (auto future : done_futures) {
    CHECK(future.Value());
  }
  LOG(INFO) << "All client SUTs have exceeded publication timeout";
  logger_->Flush();
}
