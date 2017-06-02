//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************

#include "setup-client-harness-scripts.h"

#include "modify-and-query-script.h"
#include "root-mode-master-script.h"
#include "test-harness/common/root-mode-local-script.h"
#include "test-harness/common/call-remote-script.h"
#include "test-harness/common/scripts-from-file.h"
#include "test-harness/ta1/client-sut-protocol-stack.h"
#include "test-harness/ta1/master-harness-network-listener.h"
#include "unloaded-query-latency-script.h"
#include "variable-delay-query-script.h"

void SetupClientHarnessScripts(
    ClientSUTProtocolStack* protocol_stack,
    MasterHarnessProtocolStack* network_stack,
    SUTRunningMonitor* sut_monitor,
    ScriptsFromFile* scripts_from_file) {
  scripts_from_file->AddFactory(
      "UnloadedQueryRunner",
      UnloadedQLSConstructor(protocol_stack->GetQueryCommand()));
  
  scripts_from_file->AddFactory(
      "VariableDelayQueryRunner",
      VariableDelayScriptConstructor(
          protocol_stack->GetQueryCommand()));

  scripts_from_file->AddFactory(
      "RootModeLocalScript",
      RootModeLocalScriptFromFileFactory(
            protocol_stack->GetRootModeCommandSender(),
            sut_monitor));

  if (network_stack != NULL) {
    scripts_from_file->AddFactory(
        "ModifyAndQueryScript",
        ModifyAndQueryScriptConstructor(
          network_stack->GetRunScriptCommand(),
          protocol_stack->GetQueryCommand()));

    scripts_from_file->AddFactory(
        "CallRemoteScript",
        CallRemoteScriptFileFactory(
            network_stack->GetRunScriptCommand()));

    scripts_from_file->AddFactory(
        "RootModeMasterScript",
        RootModeMasterScriptFactory(
            protocol_stack->GetRootModeCommandSender(),
            sut_monitor,
            network_stack->GetRunScriptCommand()));
  } else {
    LOG(INFO) << "No network connection. ModifyAndQueryScript not available.";
  }
}
