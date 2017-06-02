//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        For handling publication received messages.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_PUBLICATION_RECEIVED_HANDLER_H_
#define CPP_TEST_HARNESS_TA3_PUBLICATION_RECEIVED_HANDLER_H_

#include "common/protocol-extension-manager.h"
#include "common/hash-aggregator.h"
#include "common/timer.h"

class GeneralLogger;
class Knot;

/// An extension for handling publication received messages. Publication received
/// messages will consist of a PUBLICATION token, followed by a PAYLOAD token,
/// the publication's payload, an ENDPAYLOAD token, and finally an ENDPUBLICATION
/// token. The publication data is simply logged for later analysis.
class PublicationReceivedHandler : public ProtocolExtension {
 public:
  PublicationReceivedHandler(size_t sut_id, GeneralLogger* logger) : 
    sut_id_(sut_id), logger_(logger) {
    /// timer_ will be reset every time a PUBLICATION is received.
    timer_.reset(new Timer()); 
  }
  virtual ~PublicationReceivedHandler() {}

  virtual void OnProtocolStart(Knot start_line);
  virtual void LineReceived(Knot line);
  virtual void RawReceived(Knot data); 

  /// Returns true if the elapsed time on this class' timer exceeds the provided
  /// timeout argument.
  bool CheckTimeout(int timeout);
  void ResetTimer();

 private:
  size_t sut_id_;
  /// States for parsing through PUBLICATION data.
  enum State {
    WAITING_PAYLOAD, PROCESSING_PAYLOAD, WAITING_ENDPUBLICATION
  };
  State state_;
  GeneralLogger* logger_;
  /// Aggregator to build hashes on payload data.
  std::unique_ptr<HashAggregator> aggregator_;
  /// Timer to keep track of time elapsed between PUBLICATIONs.
  std::unique_ptr<Timer> timer_;
};

#endif
