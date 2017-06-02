//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A unit test fixture for things that use
//                     NumberedCommandExtension. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_COMMON_NUMBERED_COMMAND_EXTENSION_FIXTURE_H_
#define CPP_BASELINE_COMMON_NUMBERED_COMMAND_EXTENSION_FIXTURE_H_

#include "extensible-ready-handler-fixture.h"

class NumberedCommandExtensionFixture : public ExtensibleReadyHandlerFixture {
 public:
  NumberedCommandExtensionFixture() {
    command_extension = new NumberedCommandExtension(
            event_loop.GetWriteQueue(sut_stdout_write_fd));
    ready_handler->AddHandler("COMMAND", command_extension);
  }

  virtual ~NumberedCommandExtensionFixture() {}

  NumberedCommandExtension* command_extension;

};

#endif
