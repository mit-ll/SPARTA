//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Command from harness to SUT asking the SUT to update
//                     data. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************

#ifndef CPP_TEST_HARNESS_TA1_UPDATE_COMMAND_H_
#define CPP_TEST_HARNESS_TA1_UPDATE_COMMAND_H_

#include "test-harness/common/generic-numbered-command.h"

class UpdateCommand : public GenericNumberedCommand {
 public:
  UpdateCommand(NumberedCommandSender* nc, EventMessageMonitor* em = nullptr)
      : GenericNumberedCommand("UPDATE", nc, em) {}

 private:
  /// Given data, this wraps it in an UPDATE command. data is assumed to be
  /// composed of separate lines such that data.Get(0) is the row ID to update
  /// (line mode data) and is followed by a series of line pairs containing:
  ///    1) the field to update (line mode data)
  ///    2) the new field value (line mode or raw mode data)
  ///
  /// For example, data could contain the following, which updates row 7's
  /// first_name and fingerprint fields:
  ///    7
  ///    first_name
  ///    Susan
  ///    fingerprint
  ///    RAW
  ///    2
  ///    0x0091
  ///    ENDRAW
  void GetCommand(const LineRawData<Knot>& data, Knot* output);
};

#endif
