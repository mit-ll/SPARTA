//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        A simple TestScript that just passes data to a remote
//                     test harness component via RUNSCRIPT. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_CALL_REMOTE_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_CALL_REMOTE_SCRIPT_H_

#include <memory>

#include "test-harness/common/test-script.h"
#include "common/line-raw-data.h"
#include "common/knot.h"

class GeneralLogger;
class THRunScriptCommand;
class MasterHarnessNetworkListener;

/// TODO(njhwang) create unit tests
class CallRemoteScript : public TestScript {
 public:
  /// Constructor. This will use run_script_command to send command_data, which
  /// includes the name of the remote script to run, any parameters to that
  /// sctript, and the data needed by that script. This takes ownership of
  /// command_data but does *not* take ownership of run_script_command or
  /// logger.
  CallRemoteScript(std::string harness_id, 
                   MasterHarnessNetworkListener* listener,
                   GeneralLogger* logger,
                   LineRawData<Knot>* command_data) : 
    harness_id_(harness_id), listener_(listener), logger_(logger), 
    command_data_(command_data) {}

  virtual void Run();

 private:
  std::string harness_id_;
  MasterHarnessNetworkListener* listener_;
  GeneralLogger* logger_;
  std::unique_ptr<LineRawData<Knot> > command_data_;
};

/// A factory/functor for use with ScriptFromFile. config_line is expected to
/// contain a valid test harness ID matching a test harness that is being
/// controlled by listener, a space, and then a path (relative to dir_path) to a
/// file containing the LineRawData that we're going to send to the remote end to
/// run. So for example, if the MasterHarnessNetworkListener is currently
/// controlling slave harnesses with IDs "slave-1" and "slave-2", config_line
/// could be "slave-1 subscription-script", which could instruct the slave-1
/// harness to run the contents of the subscription-script config file.
class CallRemoteScriptFileFactory {
 public:
  CallRemoteScriptFileFactory(MasterHarnessNetworkListener* listener)
      : listener_(listener) {}

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path, GeneralLogger* logger);

 private:
  MasterHarnessNetworkListener* listener_;
};

#endif
