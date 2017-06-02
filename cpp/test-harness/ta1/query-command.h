//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Command that asks the SUT to query the DB with a
//                     specified query string.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************

#ifndef CPP_TEST_HARNESS_TA1_QUERY_COMMAND_H_
#define CPP_TEST_HARNESS_TA1_QUERY_COMMAND_H_

#include "common/future.h"
#include "common/knot.h"

class AggNumberedCommandSender;
class EventMessageMonitor;
class RowHashAggregator;
class GeneralLogger;

class QueryCommand {
 public:
  QueryCommand(AggNumberedCommandSender* nc,
               EventMessageMonitor* em = nullptr) : 
    nc_sender_(nc), em_monitor_(em) {}
  virtual ~QueryCommand() {}

  /// Schedules the command to execute as soon as the SUT is in the READY state.
  /// Logs when the command is scheduled to be sent, and when the command
  /// completes. When the command complete it logs the rowid and the hash of the
  /// row contents (if any) for each row returned by the SUT. This returns a
  /// Future<Knot> that will hold the rowid, hash of row pairs.
  Future<Knot> Schedule(int local_id, uint64_t query_id, const Knot& data, 
                        GeneralLogger* logger);

 private:
  /// Gets called via AggNumberedCommandSender's future when the command
  /// completes. This logs the results to logger.
  void CommandComplete(int global_id, int local_id, const Knot& results,
                       GeneralLogger* logger); 

  AggNumberedCommandSender* nc_sender_;
  EventMessageMonitor* em_monitor_;
};

#endif
