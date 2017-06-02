//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implmentation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Jan 2013   ni24039        Original Version
//*****************************************************************

#include "wait-for-final-publication-script.h"

#include "common/general-logger.h"

WaitForFinalPublicationScript::WaitForFinalPublicationScript(
      int timeout, PublicationReceivedHandler* pub_handler,
      GeneralLogger* logger)
    : timeout_(timeout), pub_handler_(pub_handler), logger_(logger) {
}

void WaitForFinalPublicationScript::Run() {
  bool final_received = false;
  LOG(INFO) << "Resetting publication received timer.";
  pub_handler_->ResetTimer();
  LOG(INFO) << "Starting timeout checks for final publication.";
  while (!final_received) {
    final_received = pub_handler_->CheckTimeout(timeout_);
  }
  LOG(INFO) << "Timeout requirement for final publication met.";
  logger_->Flush();
}
