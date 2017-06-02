//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ScriptManager 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 20 Sep 2012   omd            Original Version
//*****************************************************************

#include "script-manager.h"

using namespace std;

void ScriptManager::AddScript(const string& name,
                              ScriptFactory factory) {
  no_argument_script_map_.insert(make_pair(name, factory));
}

void ScriptManager::AddArgumentScript(
    const string& name, ArgumentScriptFactory factory) {
  argument_script_map_.insert(make_pair(name, factory));
}

auto_ptr<TestScript> ScriptManager::GetScript(const string& script) {
  map<string, ScriptFactory>::iterator i =
      no_argument_script_map_.find(script);
  CHECK(i != no_argument_script_map_.end());
  // i->second is a function. Call it and return the TestScript* it returns.
  auto_ptr<TestScript> ret(i->second());
  return ret;
}

auto_ptr<TestScript> ScriptManager::GetScript(
    const string& script, const LineRawData<Knot>& argument) {
  map<string, ArgumentScriptFactory>::iterator i =
      argument_script_map_.find(script);
  CHECK(i != argument_script_map_.end())
      << "Could not find a script named: " << script;
  // i->second is a function. Call it and return the TestScript* it returns.
  auto_ptr<TestScript> ret(i->second(argument));
  return ret;
}
