//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation for text fixtures. 
//*****************************************************************

#include "event-message-monitor-fixture.h"

#include "event-message-monitor.h"

EventMessageMonitorFixture::EventMessageMonitorFixture() {
  // Set up file descriptors for the sut's stdout
  int sut_stdout_read_fd;
  SetupPipe(&sut_stdout_read_fd, &sut_stdout_write_fd);

  // Set up file descriptors for the sut's stdin
  int sut_stdin_write_fd;
  SetupPipe(&sut_stdin_read_fd, &sut_stdin_write_fd);

  manager = new ProtocolExtensionManager;
  em_monitor = new EventMessageMonitor();
  manager->AddHandler("EVENTMSG", em_monitor);

  // Set up the parser to use the event manager.
  lr_parser.reset(new LineRawParser(manager));
  event_loop.RegisterFileDataCallback(
      sut_stdout_read_fd,
      boost::bind(&LineRawParser::DataReceived, lr_parser.get(), _1));
  event_loop.Start();
}
