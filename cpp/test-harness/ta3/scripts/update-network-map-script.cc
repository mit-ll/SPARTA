//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************

#include "update-network-map-script.h"

#include "common/general-logger.h"

UpdateNetworkMapScript::UpdateNetworkMapScript(
      size_t num_harnesses, size_t num_suts,
      MasterHarnessNetworkListener* listener, 
      GeneralLogger* logger)
    : num_harnesses_(num_harnesses), num_suts_(num_suts), 
      listener_(listener), logger_(logger) {
}

void UpdateNetworkMapScript::Run() {
  LOG(INFO) << "UpdateNetworkMapScript waiting for " 
            << num_harnesses_ << " slave harnesses to connect.";
  // TODO(njhwang) change this to just wait for num_suts_
  listener_->BlockUntilNumConnections(num_harnesses_);
  listener_->UpdateNetworkMap();
  CHECK(listener_->GetNumClientSUTs() == num_suts_) << "Only "
    << num_suts_ << " client SUTs can be connected. Detected "
    << listener_->GetNumClientSUTs() << " client SUTs";
  logger_->Flush();
}

UpdateNetworkMapScriptFactory::UpdateNetworkMapScriptFactory(
      MasterHarnessNetworkListener* listener)
    : listener_(listener) {
}

TestScript* UpdateNetworkMapScriptFactory::operator()(
    const std::string& config_line, const std::string& dir_path, 
    GeneralLogger* logger) {
  // Extract number of harness connections and client SUTs to look for.
  std::vector<std::string> parts = Split(config_line, ' ');
  CHECK(parts.size() >= 2);
  size_t num_harnesses = atoi(parts[0].c_str());
  size_t num_suts = atoi(parts[1].c_str());

  return new UpdateNetworkMapScript(
        num_harnesses, num_suts, listener_, logger);
}
