//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Test fixture for testing event message handlers.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_EVENT_MESSAGE_FIXTURE_H_
#define CPP_TEST_HARNESS_TA3_EVENT_MESSAGE_FIXTURE_H_

#include <memory>
#include <iostream>
#include <sstream>

#include "common/line-raw-parser.h"
#include "common/event-loop.h"

///class EventLoop;
class ProtocolExtensionManager;
class PublicationReceivedHandler;
class OstreamRawTimeLogger;

class EventMessageFixture {
 public:
  EventMessageFixture();
  virtual ~EventMessageFixture();

  /// Memebers are public since this is for unit tests.
  EventLoop event_loop;
  std::ostringstream* fake_log_file;
  OstreamRawTimeLogger* logger;
  int sut_stdout_write_fd;
  int sut_stdin_read_fd;
  std::unique_ptr<LineRawParser> lr_parser;
  /// The LineRawParser owns this so we don't need to free it.
  ProtocolExtensionManager* manager;
  /// The ProtocolExtensionManager has ownership of this so we don't need to free
  /// it.
  PublicationReceivedHandler* pubrecv_handler;
};

#endif
