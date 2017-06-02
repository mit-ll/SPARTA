//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Functions for creating consistent log messages. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 14 Sep 2012   omd            Original Version
// 21 Sep 2012   ni24039        Refactored to separate generic formats from TA
//                              specific formats.
//*****************************************************************************

#ifndef CPP_TEST_HARNESS_GENERIC_LOG_MESSAGE_FORMATS_H_
#define CPP_TEST_HARNESS_GENERIC_LOG_MESSAGE_FORMATS_H_

#include <sstream>
#include <string>

#include "common/general-logger.h"
#include "common/knot.h"
#include "common/line-raw-data.h"

/// We've got a number of different commands and functions all of which write log
/// messages. In order to simplify parsing those logs later we'd like to have all
/// the messages be in a consisten format. Furthermore, we'd like to be able to
/// change the format without changing all the code that writes messages. To that
/// end this file contains a set of functions which produces log messages for
/// common command types. Each TA can implement similar inline functions for TA
/// specific formats. 

/// Used by both versions of CommandCompleteMessage below. If newline is true
/// there is a \n character after "Results:". Otherwise just a space is added. If
/// local_id is < 0, it is assumed there is no valid local_id, and it will not be
/// printed.
inline Knot GetCommandCompleteHeader(int global_id, int local_id, 
                                     bool newline) {
  Knot log_message;
  char id_info_buffer[35];
  int id_info_len;
  if (local_id >= 0) {
    id_info_len = sprintf(id_info_buffer, "ID %d-%d results:", 
                          global_id, local_id);
  } else {
    id_info_len = sprintf(id_info_buffer, "ID %d results:", global_id);
  }
  log_message.Append(new std::string(id_info_buffer, id_info_len));

  if (newline) {
    log_message.AppendOwned("\n", 1);
  } else {
    log_message.AppendOwned(" ", 1);
  }

  return log_message;
}

/// TODO(njhwang) use default values for local_id, and change method prototypes
/// everywhere to allow for this
/// Same as above, but defaults local_id to -1.
inline Knot GetCommandCompleteHeader(int global_id, bool newline) {
  return GetCommandCompleteHeader(global_id, -1, newline);
}

/// Intended for use after a numbered command's results are received.
inline Knot CommandCompleteMessage(int global_id, int local_id,
                                   LineRawData<Knot> result_data) {
  Knot result = GetCommandCompleteHeader(global_id, local_id, false);
  result_data.AppendLineRawOutput(&result);
  return result;
}

/// Same as above, but defaults local_id to -1.
inline Knot CommandCompleteMessage(int global_id, 
                                   LineRawData<Knot> result_data) {
  return CommandCompleteMessage(global_id, -1, result_data);
}

/// Overloaded version of the above.
inline Knot CommandCompleteMessage(int global_id, int local_id,
                                   Knot result_data) {
  Knot result = GetCommandCompleteHeader(global_id, local_id, false);
  result.Append(result_data);
  return result;
}

/// Same as above, but defaults local_id to -1.
inline Knot CommandCompleteMessage(int global_id, Knot result_data) {
  return CommandCompleteMessage(global_id, -1, result_data);
}

/// Same as the above but puts a newline between "Results:" and the actual
/// results.
inline Knot CommandCompleteMessageWithNewline(int global_id, int local_id, 
                                              Knot result_data) {
  Knot result = GetCommandCompleteHeader(global_id, local_id, true);
  result.Append(result_data);
  return result;
}

inline Knot CommandCompleteMessageWithNewline(int global_id, Knot result_data) {
  return CommandCompleteMessageWithNewline(global_id, -1, result_data);
}

/// Intended for use after a root command's results are received.
inline Knot RootCommandCompleteMessage(const std::string& command_type,
                                       LineRawData<Knot> result_data) {
  Knot result;
  static const char kCommandHeader[] = "Root command ";
  static const int kCommandHeaderLen = strlen(kCommandHeader);
  result.AppendOwned(kCommandHeader, kCommandHeaderLen);
  result.Append(new std::string(command_type));

  static const char kCompleteHeader[] = " complete. Results: ";
  static const int kCompleteHeaderLen = strlen(kCompleteHeader);
  result.AppendOwned(kCompleteHeader, kCompleteHeaderLen);

  result_data.AppendLineRawOutput(&result);
  return result;
}

/// Intended for use after a root command is sent.
inline Knot RootCommandSentMessage(const std::string& command_type) {
  Knot result;
  static const char kCommandHeader[] = "Root command ";
  static const int kCommandHeaderLen = strlen(kCommandHeader);
  result.AppendOwned(kCommandHeader, kCommandHeaderLen);
  result.Append(new std::string(command_type));

  static const char kSentHeader[] = " sent";
  static const int kCompleteSentLen = strlen(kSentHeader);
  result.AppendOwned(kSentHeader, kCompleteSentLen);

  return result;
}

/// Intended to be sent when a command gets queued for transmission. Note that
/// when commands are queued, they will not have a global_id assigned to them, so
/// a '?' is used in place of a global_id.
inline Knot CommandQueuedMessage(int local_id) {
  Knot log_message;
  char id_info_buffer[25];
  int id_info_len;
  id_info_len = sprintf(id_info_buffer, "ID ?-%d queued", local_id);
  log_message.Append(new std::string(id_info_buffer, id_info_len));

  return log_message;
}

/// Intended to describe the contents of a numbered command that is part of a
/// particular command group. For example, query commands are usually sent from a
/// script that contains multiple commands. This message specifies both the
/// 'global' ID for each command (i.e., the global command counter value) and the
/// 'local' ID (i.e., the location of the command in the currently executing
/// script). If local_id is < 0, it is assumed there is no valid local_id, and it
/// will not be printed.
inline Knot CommandDescMessage(const std::string& message,
                               int global_id, int local_id = -1) {
  Knot log_message;
  char id_info_buffer[25];
  int id_info_len;
  if (local_id >= 0) {
    id_info_len = sprintf(id_info_buffer, "ID %d-%d ", 
                          global_id, local_id);
  } else {
    id_info_len = sprintf(id_info_buffer, "ID %d ", global_id);
  }
  log_message.Append(new std::string(id_info_buffer, id_info_len));
  log_message.Append(new std::string(message));

  return log_message;
}

/// A functor that can be passed as the SentCallback to AggNumberedCommandSender
/// or NumberedCommandSender's SendCommand() method.  This logs a command
/// description, and that the command was sent.  Intended to log the transmission
/// of numbered commands that also have a local count associated with them.
class LogNumberedCommandSent {
 public:
  LogNumberedCommandSent(GeneralLogger* logger, 
                         int local_id, 
                         const Knot& desc) : 
    logger_(logger), local_id_(local_id), desc_(desc) {}
  void operator()(int global_id) {
    logger_->Log(CommandDescMessage(desc_.ToString(), global_id, local_id_));

    /// TODO(njhwang) not consistent with how we use knots to build the other
    /// logging strings. Figure out what's faster, and go with that.
    std::ostringstream output;
    if (local_id_ >= 0) {
      output << "ID " << global_id << "-" << local_id_ << " sent";
    } else {
      output << "ID " << global_id << " sent";
    }
    logger_->Log(output.str());
  }

 private:
  GeneralLogger* logger_;
  int local_id_;
  Knot desc_;
};

class LogEventMessage {
 public:
  LogEventMessage(GeneralLogger* logger, 
                  int local_id) : 
    logger_(logger), local_id_(local_id) {}
  void operator()(int global_id, int event_id, Knot info) {
    /// TODO(njhwang) not consistent with how we use knots to build the other
    /// logging strings. Figure out what's faster, and go with that.
    std::ostringstream output;
    if (local_id_ >= 0) {
      output << "ID " << global_id << "-" << local_id_;
    } else {
      output << "ID " << global_id;
    }
    output << " event " << event_id;
    if (info.Size() > 0) {
      output << " with value [[" << info << "]]";
    }
    output << " occurred";
    logger_->Log(output.str());
  }

 private:
  GeneralLogger* logger_;
  int local_id_;
};

#endif
