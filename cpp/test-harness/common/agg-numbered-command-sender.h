//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Like NumberedCommandSender but this allows the user use
//                     an aggregating future to pre-aggregate the results.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_AGG_NUMBERED_COMMAND_SENDER_H_
#define CPP_TEST_HARNESS_COMMON_AGG_NUMBERED_COMMAND_SENDER_H_

#include <memory>
#include <thread>
#include <map>

#include "numbered-command-sender-base.h"
#include "common/aggregating-future.h"
#include "common/knot.h"

template<class AggT> class PartialFutureAggregator;
class EventMessageMonitor;
class GeneralLogger;
class ReadyMonitor;

/// In general, this is like NumberedCommandSender but instead of SendCommand
/// returning a Future, SendCommand takes a PartialFutureAggregator so that
/// results can be aggregated as they arrive.
///
/// Note: NumberedCommandSender inherits from MultiNumberedCommandSender.
/// However, a FutureAggregator really only makes sense if it's aggregating
/// results for a single command. Trying to update MultiNumberedCommand sender so
/// it could optionally take a PartialFutureAggregator seemed really messy and
/// unnatural, and it significantly complicated the code. Thus it was decided
/// that a separate class made more sense.
class AggNumberedCommandSender : public NumberedCommandSenderBase {
 public:
  AggNumberedCommandSender(ReadyMonitor* ready_monitor, 
                           EventMessageMonitor* event_monitor = nullptr);
  virtual ~AggNumberedCommandSender();

  /// This takes ownership of aggregator and frees it some time after Done() is
  /// called on the aggregator. 
  ///
  /// sent_cb is called when the READY signal is received and the command is
  /// actually sent. It gets called with the command_id of the command that was
  /// sent. See LogNumberedCommandSent in generic-log-message-formats.h as an
  /// example.
  ///
  /// event_cb is called whenever an EVENTMSG signal is fully received. Since
  /// EVENTMSGs can interrupt a RESULTS block, AggNumberedCommandSender must be
  /// able to know what to do in the event of an EVENTMSG signal. This callback
  /// gets called with the command_id of the command that was sent, the event ID
  /// of the EVENTMSG received, and a Knot containing any other details of the
  /// EVENTMSG.
  typedef std::function<void (int, int, Knot)> EventCallback;
  typedef std::function<void (int)> SentCallback;
  void SendCommand(Knot data, 
                   std::unique_ptr<PartialFutureAggregator<Knot> > aggregator,
                   int* command_id,
                   SentCallback sent_cb = nullptr, 
                   EventCallback event_cb = nullptr);

 protected:
  virtual void OnProtocolStartImpl(int command_id);
  virtual void LineReceivedImpl(Knot line);
  virtual void RawReceivedImpl(Knot data);
  virtual void ResultsDone();

 private:
  std::mutex data_tex_;
  std::map<int, PartialFutureAggregator<Knot>* > agg_map_;
  PartialFutureAggregator<Knot>* cur_agg_;
  int cur_command_id_;
  bool parsing_eventmsg_;
  EventMessageMonitor* event_monitor_;
};

#endif
