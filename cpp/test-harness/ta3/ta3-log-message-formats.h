//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Functions for creating consistent log messages. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#ifndef CPP_TEST_HARNESS_TA3_LOG_MESSAGE_FORMATS_H_
#define CPP_TEST_HARNESS_TA3_LOG_MESSAGE_FORMATS_H_

#include <string>

#include "test-harness/common/generic-log-message-formats.h"
#include "common/line-raw-data.h"
#include "common/knot.h"

/// Intended for use after a PUBLICATION event message is received.
inline Knot PublicationReceivedMessage(size_t sut_id, Knot data) {
  Knot result;
  result.Append(new std::string("Publication received on SUT " +
        itoa(sut_id) + ". Payload hash: "));
  result.Append(data);
  return result;
}

/// Intended for use after a DISCONNECTION event message is received.
inline Knot DisconnectionReceivedMessage(size_t sut_id) {
  Knot result;
  result.Append(new std::string("SUT " + itoa(sut_id) + 
        " lost connection to server."));
  return result;
}

/// Intended for use after a PUBLISH command gets sent.
inline Knot PublishCommandSentMessage(int command_id, 
                                      size_t payload_length,
                                      Knot metadata,
                                      Knot hash) {
  Knot result = RootCommandSentMessage("PUBLISH");

  static const char kCommandIdHeader[] = ", command id: ";
  static const int kCommandIdHeaderLen = strlen(kCommandIdHeader);
  result.AppendOwned(kCommandIdHeader, kCommandIdHeaderLen);
  result.Append(new std::string(itoa(command_id)));

  static const char kMetadataHeader[] = ", metadata: ";
  static const int kMetadataHeaderLen = strlen(kMetadataHeader);
  result.AppendOwned(kMetadataHeader, kMetadataHeaderLen);
  result.Append(metadata);

  static const char kHashHeader[] = ", payload hash: ";
  static const int kHashHeaderLen = strlen(kHashHeader);
  result.AppendOwned(kHashHeader, kHashHeaderLen);
  result.Append(hash);

  static const char kLengthHeader[] = ", payload length: ";
  static const int kLengthHeaderLen = strlen(kLengthHeader);
  result.AppendOwned(kLengthHeader, kLengthHeaderLen);
  result.Append(new std::string(itoa(payload_length)));

  return result;
}

#endif
