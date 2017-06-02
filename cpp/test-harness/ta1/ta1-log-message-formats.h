//******************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Functions for creating consistent log messages. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original version (code taken from OMD's
//                              original)
//                              log-message-formats.h.
//******************************************************************************

#ifndef CPP_TEST_HARNESS_TA1_LOG_MESSAGE_FORMATS_H_
#define CPP_TEST_HARNESS_TA1_LOG_MESSAGE_FORMATS_H_

#include <string>

#include "common/knot.h"
#include "common/string-algo.h"
#include "test-harness/common/generic-log-message-formats.h"

/// Implements TA1 specific log message formats. See comments in
/// ../common/generic-log-message-formats.h.
/// A log message for insert, update, and delete commands. Params:
///
/// command_type: INSERT, UPDATE, or DELETE
/// global_id: the id of the numbered command that was sent
/// row_id: the primary key of the affected row.
inline Knot DBModifyCommandSentMessage(
    std::string command_type, int global_id, int mod_id, int row_id) {
  DCHECK(command_type == "INSERT" ||
         command_type == "UPDATE" ||
         command_type == "DELETE");
  std::string desc_message("MID ");
  desc_message += itoa(mod_id);
  desc_message += ": ";
  desc_message += command_type;
  desc_message += " ";
  desc_message += itoa(row_id);
  return CommandDescMessage(desc_message, global_id);

  /*static const char kRowHeader[] = ", row: ";
  static const int kRowHeaderLen = strlen(kRowHeader);
  result.AppendOwned(kRowHeader, kRowHeaderLen);
  result.Append(row_id);
  return result;*/
}

#endif
