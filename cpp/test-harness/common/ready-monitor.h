//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A ReadyMonitor class to keep track of the ready state of
//                     the SUT. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Jul 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_READY_MONITOR_H_
#define CPP_TEST_HARNESS_COMMON_READY_MONITOR_H_

#include <boost/thread.hpp>
#include <deque>
#include <string>

#include "common/conditions.h"
#include "common/event-loop.h"
#include "common/protocol-extension-manager.h"

/// This class serves two purposes. First, it is a ProtocolExtension that handles
/// the "READY" protocol. Second, since it tracks when the SUT is in the READY
/// state it is used by all protocols that send data to the SUT to ensure that
/// data is sent only when the SUT is in the READY state.
///
/// To use, register this with the ProtocolExtensionManager so it gets notified
/// when "READY" is received. Then, give an instance of this class to all other
/// protocols that need to send data to the SUT. Those protocols send data to the
/// SUT by calling either BlockUntilReadyAndSend() or ScheduleSend(). The former
/// blocks until the SUT is in the ready state and then sends the SUT the
/// requested data while the latter schedules the data to be sent as soon as
/// possible and returns immediately.
class ReadyMonitor : public ProtocolExtension {
 public:
  /// Constructor. The output_queue should be configured with the file handle for
  /// the SUT's stdin. This queue is used by BlockUntilReadyAndSend and
  /// ScheduleSend to send the data to the SUT.
  ReadyMonitor(WriteQueue* output_queue);
  virtual ~ReadyMonitor();
  /// Returns the current ready state of the SUT. Note that by the time this
  /// method returns the ready state may have changed.
  bool IsReady() const;
  /// Blocks until the SUT is in the READY state. Note that if there are multiple
  /// threads there is no guarantee that the SUT will still be in the READY state
  /// by the time this method returns. The main use case is waiting for the
  /// initial READY before beginning a test.
  void WaitUntilReady() const;

  /// Called by ProtocolExtensionManager when READY is received.
  virtual void OnProtocolStart(Knot start_line);
  /// Blocks until the SUT is ready and then sends the data. Takes ownership of
  /// to_send.
  void BlockUntilReadyAndSend(Knot* to_send);

  /// Send as soon as possible. Does not block. Returns immediately. Takes
  /// ownership of to_send.  Calls cb just before sending the command (when the
  /// SUT enters the ready state but before actually wirting the data). We
  /// call before writing as the system call might take some time. What we really
  /// want to record is the time between the "user" sending a command and it
  /// getting executed. But more than anything, all that matters is that we're
  /// consistent in how we measure the baseline and the performer's systems.
  typedef std::function<void ()> SentCallback;
  void ScheduleSend(Knot* to_send, SentCallback cb);
  /// The same as the above but without a callback.
  void ScheduleSend(Knot* to_send) {
    ScheduleSend(to_send, nullptr);
  }

 private:
  /// Pop an item off the front of the send_queue_ and write it to the SUT. Note
  /// this method does not acquire data_tex_. The calling method must hold it.
  void WriteQueuedItem();

  /// The WriteQueue used for sending all data.
  WriteQueue* write_queue_;
  /// Guards all the data members below.
  mutable boost::mutex data_tex_;
  typedef boost::lock_guard<boost::mutex> MutexGuard;

  /// The current ready state of the SUT.
  bool ready_;
  /// Used to signal blocking calls when ready_ becomes true.
  mutable boost::condition_variable ready_cond_;

  struct SendQueueItem {
    /// Construct an item to be queued for sending. ts is the data to send and sc
    /// is a condition variable. If it is not NULL it will be notified when the
    /// data has been sent.
    SendQueueItem(Knot* ts,
                  SimpleCondition<bool>* sc);
    SendQueueItem(Knot* ts,
                  SimpleCondition<bool>* sc,
                  SentCallback cb);
    Knot* to_send;
    SimpleCondition<bool>* sent_cond;
    SentCallback sent_cb;
  };
  /// Queue of items that need to be sent to the SUT as soon as it enters the
  /// ready state.
  std::deque<SendQueueItem*> send_queue_;
};

#endif
