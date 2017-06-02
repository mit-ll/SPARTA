//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A simple TestScript that just passes data to a remote
//                     test harness component via RUNSCRIPT. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_CALL_REMOTE_SCRIPT_H_
#define CPP_TEST_HARNESS_COMMON_CALL_REMOTE_SCRIPT_H_

#include <memory>

#include "common/knot.h"
#include "common/line-raw-data.h"
#include "test-script.h"

class GeneralLogger;
class THRunScriptCommand;

class CallRemoteScript : public TestScript {
 public:
  /// Constructor. This will use run_script_command to send command_data, which
  /// includes the name of the remote script to run, any parameters to that
  /// sctript, and the data needed by that script. This takes ownership of
  /// command_data but does *not* take ownership of run_script_command or
  /// logger.
  CallRemoteScript(THRunScriptCommand* run_script_command,
                   GeneralLogger* logger,
                   LineRawData<Knot>* command_data);

  virtual void Run();

 private:
  THRunScriptCommand* run_script_command_;
  GeneralLogger* logger_;
  std::unique_ptr<LineRawData<Knot> > command_data_;
};

/// A factory/functor for use with ScriptFromFile. This expects the argument to
/// be a path, relative to dir_path, to a file containing the LineRawData that
/// we're going to send to the remote end to run.
class CallRemoteScriptFileFactory {
 public:
  CallRemoteScriptFileFactory(THRunScriptCommand* run_script_command)
      : run_script_command_(run_script_command) {}

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path,
                         GeneralLogger* logger);

 private:
  THRunScriptCommand* run_script_command_;
};

#endif
