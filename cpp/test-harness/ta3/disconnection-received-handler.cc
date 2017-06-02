//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of DisconnectionReceivedHandler.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "disconnection-received-handler.h"
#include "slave-harness-network-stack.h"
#include "ta3-log-message-formats.h"
#include "common/general-logger.h"
#include "common/line-raw-data.h"
#include "common/knot.h"

using namespace std;

const char kDisconnection[] = "DISCONNECTION";
const int kDisconnectionLen = strlen(kDisconnection);

void DisconnectionReceivedHandler::OnProtocolStart(Knot line) {
  DCHECK(line.Equal(kDisconnection, kDisconnectionLen));
  logger_->Log(DisconnectionReceivedMessage(sut_id_));
  network_stack_->SUTDisconnected(sut_id_);
  Done();
}

void DisconnectionReceivedHandler::LineReceived(Knot line) {
  LOG(FATAL) << "DISCONNECTION message should be a single line.";
}

void DisconnectionReceivedHandler::RawReceived(Knot data) {
  LOG(FATAL) << "DISCONNECTION message should be a single line.";
}
