//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of PublicationReceivedHandler.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "publication-received-handler.h"
#include "ta3-log-message-formats.h"
#include "common/general-logger.h"
#include "common/line-raw-data.h"
#include "common/knot.h"

using namespace std;

const char kPublication[] = "PUBLICATION";
const int kPublicationLen = strlen(kPublication);

void PublicationReceivedHandler::OnProtocolStart(Knot line) {
  DCHECK(line.Equal(kPublication, kPublicationLen));
  state_ = WAITING_PAYLOAD;
}

void PublicationReceivedHandler::LineReceived(Knot line) {
  switch (state_) {
    case WAITING_PAYLOAD:
      CHECK(line == "PAYLOAD");
      state_ = PROCESSING_PAYLOAD;
      aggregator_.reset(new HashAggregator()); 
      break;
    case PROCESSING_PAYLOAD:
      if (line == "ENDPAYLOAD") {
        state_ = WAITING_ENDPUBLICATION;
      } else {
        aggregator_->AddPartialResult(line);
      }
      break;
    case WAITING_ENDPUBLICATION:
      CHECK(line == "ENDPUBLICATION");
      aggregator_->Done();
      logger_->Log(PublicationReceivedMessage(sut_id_, 
                      aggregator_->GetFuture().Value()));
      Done();
      timer_.reset(new Timer());
      timer_->Start();
      break;
    default:
      LOG(FATAL) << "This shouldn't ever happen!";
  }
}

void PublicationReceivedHandler::RawReceived(Knot data) {
  CHECK(state_ == PROCESSING_PAYLOAD) << "Should only receive raw mode data" <<
    " in the PAYLOAD portion of the PUBLICATION event message";
  aggregator_->AddPartialResult(data);
}

bool PublicationReceivedHandler::CheckTimeout(int timeout) {
  return (timer_->Elapsed() > double(timeout));
}

void PublicationReceivedHandler::ResetTimer() {
  timer_.reset(new Timer());
  timer_->Start();
}
