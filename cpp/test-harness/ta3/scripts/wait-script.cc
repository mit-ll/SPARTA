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

#include "wait-script.h"
#include "common/string-algo.h"
#include <boost/thread.hpp>
#include "common/general-logger.h"

void WaitScript::Run() {
  LOG(INFO) << "WaitScript waiting for " << num_secs_;
  boost::this_thread::sleep(boost::posix_time::seconds(num_secs_));
  logger_->Flush();
}

TestScript* WaitScriptFactory::operator()(
    const std::string& config_line, const std::string& dir_path, 
    GeneralLogger* logger) {
  return new WaitScript(SafeAtoi(config_line), logger);
}
