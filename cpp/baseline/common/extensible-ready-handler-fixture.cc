//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ExtensibleReadyHandlerFixture 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   omd            Original Version
//*****************************************************************

#include "extensible-ready-handler-fixture.h"

ExtensibleReadyHandlerFixture::ExtensibleReadyHandlerFixture() {
  // Set up file descriptors for the sut's stdout
  SetupPipe(&sut_stdout_read_fd, &sut_stdout_write_fd);

  // Set up file descriptors for the sut's stdin
  SetupPipe(&sut_stdin_read_fd, &sut_stdin_write_fd);

  ready_handler = new ExtensibleReadyHandler(
      event_loop.GetWriteQueue(sut_stdout_write_fd));

  // Set up the parser to use the event manager.
  lr_parser.reset(new LineRawParser(ready_handler));
  event_loop.RegisterFileDataCallback(
      sut_stdin_read_fd,
      boost::bind(&LineRawParser::DataReceived, lr_parser.get(), _1));
  event_loop.Start();

}
