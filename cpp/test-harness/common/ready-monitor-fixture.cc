//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation for text fixtures. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Sep 2012   omd            Original Version
//*****************************************************************

#include "ready-monitor-fixture.h"

#include "ready-monitor.h"

// Sets up the whole hierarchy of event loop, LineRawParser,
// ProtocolExtensionManager, and finally ReadyMonitor. All the paramters to this
// are output parameters which get set in this method.
ReadyMonitorFixture::ReadyMonitorFixture() {
  // Set up file descriptors for the sut's stdout
  int sut_stdout_read_fd;
  SetupPipe(&sut_stdout_read_fd, &sut_stdout_write_fd);

  // Set up file descriptors for the sut's stdin
  int sut_stdin_write_fd;
  SetupPipe(&sut_stdin_read_fd, &sut_stdin_write_fd);

  manager = new ProtocolExtensionManager;
  ready_monitor = new ReadyMonitor(
      event_loop.GetWriteQueue(sut_stdin_write_fd));
  manager->AddHandler("READY", ready_monitor);

  // Set up the parser to use the event manager.
  lr_parser.reset(new LineRawParser(manager));
  event_loop.RegisterFileDataCallback(
      sut_stdout_read_fd,
      boost::bind(&LineRawParser::DataReceived, lr_parser.get(), _1));
  event_loop.Start();
}
