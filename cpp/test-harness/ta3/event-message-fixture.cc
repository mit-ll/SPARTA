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

#include "event-message-fixture.h"
#include "publication-received-handler.h"
#include "common/general-logger.h"
#include "common/util.h"

EventMessageFixture::EventMessageFixture() {
  size_t sut_id = 0;
  fake_log_file = new std::ostringstream;
  logger = new OstreamRawTimeLogger(fake_log_file);

  // Set up file descriptors for the sut's stdout
  int sut_stdout_read_fd;
  SetupPipe(&sut_stdout_read_fd, &sut_stdout_write_fd);

  // Set up file descriptors for the sut's stdin
  int sut_stdin_write_fd;
  SetupPipe(&sut_stdin_read_fd, &sut_stdin_write_fd);

  manager = new ProtocolExtensionManager;
  pubrecv_handler = new PublicationReceivedHandler(sut_id, logger);
  manager->AddHandler("PUBLICATION", pubrecv_handler);
  // TODO(njhwang) add testing of DISCONNECTION

  // Set up the parser to use the event manager.
  lr_parser.reset(new LineRawParser(manager));
  event_loop.RegisterFileDataCallback(
      sut_stdout_read_fd,
      boost::bind(&LineRawParser::DataReceived, lr_parser.get(), _1));
  event_loop.Start();
}

EventMessageFixture::~EventMessageFixture() {
  event_loop.ExitLoopAndWait();
  delete logger;
}

