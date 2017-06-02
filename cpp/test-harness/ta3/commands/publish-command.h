//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Command from harness to SUT asking the SUT 
//                     to publish given metadata and payload. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_PUBLISH_COMMAND_H_
#define CPP_TEST_HARNESS_TA3_PUBLISH_COMMAND_H_

#include "test-harness/common/generic-numbered-command.h"

class PublishCommand : public GenericNumberedCommand {
 public:
  PublishCommand(NumberedCommandSender* nc)
      : GenericNumberedCommand("PUBLISH", nc) {}

 private:
  /// Given data, this wraps it in a PUBLISH command. data is assumed to be such
  /// that data.Get(0) returns the publication's metadata (without an EOL
  /// character), and data.Get(1) returns the publication's payload; the caller
  /// of GetCommand is responsible for ensuring that data.Get(1) either has
  /// properly formatted raw mode data, or line mode data with an EOL character
  /// included.
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output);
  virtual void LogCommandDesc(int global_id, int local_id, 
                              const LineRawData<Knot>& data, 
                              GeneralLogger* logger);
};

#endif
