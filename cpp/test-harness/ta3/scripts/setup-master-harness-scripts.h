//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Function to setup server harness scripts.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_SETUP_MASTER_HARNESS_SCRIPTS_H_
#define CPP_TEST_HARNESS_TA3_SETUP_MASTER_HARNESS_SCRIPTS_H_

#include "update-network-map-script.h"
#include "root-mode-master-script.h"
#include "publish-script.h"
#include "publish-and-modify-subscriptions-script.h"
#include "call-remote-script.h"
#include "wait-script.h"
#include "test-harness/ta3/master-harness-network-listener.h"
#include "test-harness/ta3/server-sut-protocol-stack.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/scripts-from-file.h"
#include "common/event-loop.h"

/// Given a ScriptsFromFile instance this sets up the set of scripts the client
/// harness needs to be able to parse out of a configuration file and run. The
/// protocol, listener and logger items are necessary for some of the factory
/// functors.
void SetupMasterHarnessScripts(ServerSUTProtocolStack* sut_protocols,
                  MasterHarnessNetworkListener* listener,
                  ScriptsFromFile* scripts_from_file,
                  SUTRunningMonitor* sut_running,
                  FirstTokenRawTimeLogFileGenerator* logger_factory, 
                  unsigned int timestamp_period) {
  scripts_from_file->AddFactory("UpdateNetworkMap",
    UpdateNetworkMapScriptFactory(listener));
  
  scripts_from_file->AddFactory("CallRemoteScript",
    CallRemoteScriptFileFactory(listener));

  scripts_from_file->AddFactory("RootModeMasterScript",
      RootModeMasterScriptFactory(
          sut_protocols->GetRootModeCommandSender(), sut_running, listener));

  scripts_from_file->AddFactory("PublishScript",
      PublishScriptFactory(sut_protocols->GetPublishCommand()));

  scripts_from_file->AddFactory("WaitScript",
      WaitScriptFactory());

  scripts_from_file->AddFactory("PublishAndModifySubscriptionsScript",
      PublishAndModifySubscriptionsScriptFactory(
        sut_protocols->GetPublishCommand(),
        listener, logger_factory, timestamp_period));
}

#endif
