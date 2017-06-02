//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ReadyMonitor. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Jul 2012   omd            Original Version
//*****************************************************************

#include "ready-monitor.h"

#include "common/check.h"
#include "common/logging.h"

using std::string;

ReadyMonitor::ReadyMonitor(WriteQueue* output_queue)
    : write_queue_(output_queue), ready_(false) {

}

ReadyMonitor::~ReadyMonitor() {
  MutexGuard l(data_tex_);
  CHECK(send_queue_.size() == 0) << "Destroying ReadyMonitor that still "
      << "has items in its output queue.";
}

void ReadyMonitor::OnProtocolStart(Knot start_line) {
  DCHECK(start_line == "READY");
  MutexGuard l(data_tex_);
  CHECK(ready_ == false) << "Recevied a READY token for a SUT that is "
      << "already in the ready state.";
  if (send_queue_.size() > 0) {
    // If there are queued items we write the 1st one and we do not put the SUT
    // back in the ready state as the newly written item puts it back in the
    // unready state.
    WriteQueuedItem();
  } else {
    // Noting queued so the SUT is ready.
    ready_ = true;
    ready_cond_.notify_all();
  }
  Done();
}

void ReadyMonitor::WriteQueuedItem() {
  DCHECK(send_queue_.size() > 0);
  SendQueueItem* item = send_queue_.front();
  if (item->sent_cb) {
    // Call the users callback before sending the data
    item->sent_cb();
  }

  // I think write() shouldn't ever return false here. If the SUT has indicated
  // it's READY that should mean it is ready to handle the next command.
  bool write_res = write_queue_->Write(item->to_send);
  CHECK(write_res == true) << "Write to SUT failed. Tried to write:\n"
      << *item->to_send;
  if (item->sent_cond != NULL) {
   item->sent_cond->Set(true);
  } 
  // Does not free the Knot* as the WriteQueue handles that.
  delete item;
  send_queue_.pop_front();
}

bool ReadyMonitor::IsReady() const {
  MutexGuard l(data_tex_);
  return ready_;
}

void ReadyMonitor::WaitUntilReady() const {
  boost::unique_lock<boost::mutex> lock(data_tex_);
  while (!ready_) {
    ready_cond_.wait(lock);
  }
}

void ReadyMonitor::BlockUntilReadyAndSend(Knot* to_send) {
  DCHECK(to_send != NULL);
  DCHECK(to_send->Size() > 0);
  data_tex_.lock();
  if (ready_) {
    bool write_res = write_queue_->Write(to_send);
    CHECK(write_res) << "SUT indicated READY but Write to SUT failed.";
    ready_ = false;
    data_tex_.unlock();
  } else {
    SimpleCondition<bool> sent_cond(false);
    send_queue_.push_back(new SendQueueItem(to_send, &sent_cond));
    data_tex_.unlock();
    sent_cond.Wait(true);
  }
}

void ReadyMonitor::ScheduleSend(Knot* to_send, SentCallback cb) {
  DCHECK(to_send != NULL);
  DCHECK(to_send->Size() > 0);
  MutexGuard l(data_tex_);
  if (ready_) {
    if (cb) {
      cb();
    }
    bool write_res = write_queue_->Write(to_send);
    CHECK(write_res) << "SUT indicated READY but Write to SUT failed.";
    ready_ = false;
  } else {
    send_queue_.push_back(new SendQueueItem(to_send, nullptr, cb));
  }
}

////////////////////////////////////////////////////////////////////////////////
// SendQueueItem implementation
////////////////////////////////////////////////////////////////////////////////

ReadyMonitor::SendQueueItem::SendQueueItem(
    Knot* ts, SimpleCondition<bool>* sc) : to_send(ts), sent_cond(sc) {
}

ReadyMonitor::SendQueueItem::SendQueueItem(
    Knot* ts, SimpleCondition<bool>* sc, SentCallback cb)
    : to_send(ts), sent_cond(sc), sent_cb(cb) {
}
