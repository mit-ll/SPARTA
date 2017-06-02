//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Maintains the set of available and running scripts. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 20 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_BASELINE_COMMON_SCRIPT_MANAGER_H_
#define CPP_BASELINE_COMMON_SCRIPT_MANAGER_H_

#include <boost/function.hpp>
#include <map>
#include <string>

#include "test-script.h"
#include "common/knot.h"
#include "common/line-raw-data.h"

/// A script manager maintains a map from script name to a factory function that
/// can construct the relevant type of script. There are two general script
/// classes, those that take arguments, and those that don't. Argument scripts
/// require a LineRawData<Knot> instance be passed to their factory so they can
/// be properly instantiated. For example, the UnloadedModifyArgumentScript
/// requires LineRawData<Knot> detailing the set of modifications the script is
/// to perform.
///
/// This class is generally used by test harness components that listen for
/// commands from a "master" test harness component. The master sends LineRawData
/// indicating what commands should be sent to the SUT, and the corresponding
/// test harness scripts are instantiated via the ScriptManager. For example, see
/// THRunScriptHandler in test-harness/common/th-run-script-handler.h.
class ScriptManager {
 public:
  typedef boost::function<TestScript* ()> ScriptFactory;
  /// Add a regular script.
  void AddScript(const std::string& name,
                 ScriptFactory script_factory);

  /// The factory will be called with a LineRawData that has has SetStartOffset
  /// and SetEndOffset called so as to remove any RUNSCRIPT/ENDRUNSCRIPT, script
  /// name, or other wrappers. The data passed is data relevant to the script
  /// factory itself.
  typedef boost::function<TestScript* (const LineRawData<Knot>&)>
        ArgumentScriptFactory;
  /// Add a script that takes arguments.
  void AddArgumentScript(const std::string& name,
                         ArgumentScriptFactory script_factory);

  std::auto_ptr<TestScript> GetScript(const std::string& script);
  std::auto_ptr<TestScript> GetScript(const std::string& script,
                                      const LineRawData<Knot>& argument);

 private:
  std::map<std::string, ScriptFactory> no_argument_script_map_;
  std::map<std::string, ArgumentScriptFactory> argument_script_map_;
};


#endif
