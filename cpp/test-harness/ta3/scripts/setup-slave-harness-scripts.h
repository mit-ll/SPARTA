//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Builds the set of scripts the client harness can handle. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_SETUP_SLAVE_HARNESS_SCRIPTS_H_
#define CPP_TEST_HARNESS_TA3_SETUP_SLAVE_HARNESS_SCRIPTS_H_

#include "multi-wait-for-final-publication-script.h"
#include "root-mode-multi-client-local-script.h"
#include "unsubscribe-script.h"
#include "subscribe-script.h"
#include "test-harness/ta3/multi-client-sut-protocol-stack.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/script-manager.h"
#include "common/general-logger.h"
#include "common/event-loop.h"

/// Given a ScriptsFromFile instance this sets up the set of scripts the client
/// harness needs to be able to parse out of a configuration file and run. The
/// protocol and logger items are necessary for some of the factory functors.
void SetupSlaveHarnessScripts(
    MultiClientSUTProtocolStack* protocol_stack, GeneralLogger* logger,
    ScriptManager* script_manager,
    std::vector<SUTRunningMonitor*> sut_monitors) {
  
  script_manager->AddArgumentScript(
      "SubscribeScript",
      SubscribeScriptFactory(protocol_stack, logger));

  script_manager->AddArgumentScript(
      "UnsubscribeScript",
      UnsubscribeScriptFactory(protocol_stack, logger));

  script_manager->AddArgumentScript(
      "RootModeMultiClientLocalScript",
      RootModeMultiClientLocalScriptFactory(protocol_stack, logger,
                                            sut_monitors));

  script_manager->AddArgumentScript(
      "MultiWaitForFinalPublicationScript",
      MultiWaitForFinalPublicationScriptFactory(protocol_stack, logger));
}

#endif
