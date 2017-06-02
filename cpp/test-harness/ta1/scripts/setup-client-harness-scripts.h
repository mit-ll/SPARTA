//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Builds the set of scripts the client harness can
//                     handle. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_SCRIPTS_SETUP_CLIENT_HARNESS_SCRIPTS_H_
#define CPP_TEST_HARNESS_TA1_SCRIPTS_SETUP_CLIENT_HARNESS_SCRIPTS_H_

class ClientSUTProtocolStack;
class GeneralLogger;
class MasterHarnessProtocolStack;
class ScriptsFromFile;
class SUTRunningMonitor;

/// Given a ScriptsFromFile instance this sets up the set of scripts the client
/// harness needs to be able to parse out of a configuration file and run. The
/// protocol and logger items are necessary for some of the factory functors.
void SetupClientHarnessScripts(
    ClientSUTProtocolStack* protocol_stack,
    MasterHarnessProtocolStack* network_stack,
    SUTRunningMonitor* sut_monitor,
    ScriptsFromFile* scripts_from_file);

#endif
