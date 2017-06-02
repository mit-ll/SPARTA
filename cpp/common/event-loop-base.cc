//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of EventLoopBase 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Oct 2012   omd            Original Version
//*****************************************************************

#include "event-loop-base.h"

#include <event2/thread.h>

#include "check.h"
#include "logging.h"
#include "statics.h"
#include "types.h"

////////////////////////////////////////////////////////////////////////////////
// EventLoopBase
////////////////////////////////////////////////////////////////////////////////

EventLoopBase::EventLoopBase()
    : event_base_(event_base_new()),
      master_event_(new FakeEvent(event_base_)) {
  master_event_->Add();
  CHECK(event_base_ != NULL);
}

EventLoopBase::~EventLoopBase() {
  CHECK(event_loop_thread_.get() != NULL);
  CHECK(event_loop_thread_->joinable() == false)
    << "EventLoopBase destructor called but event loop thread not complete.";

  // We have to free the FakeEvent before the event_base gets freed so we do it
  // here explicitly.
  master_event_.reset();
  event_base_free(event_base_);
}

void EventLoopBase::ExitLoop() {
  // Note that this has no effect if the event was already deleted so it is safe
  // to call this more than once.
  master_event_->Remove();
}

void EventLoopBase::WaitForExit() {
  CHECK(event_loop_thread_.get() != NULL);
  // Wait for the event loop thread to exit.
  event_loop_thread_->join();
}

void EventLoopBase::Start() {
  CHECK(event_loop_thread_.get() == NULL);
  event_loop_thread_.reset(new boost::thread(
          boost::bind(&EventLoopBase::RunTheLoop, this)));
}

void EventLoopBase::RunTheLoop() {
  event_base_dispatch(event_base_);
}

void EventLoopBase::RegisterEvent(event* event_to_register) {
  event_add(event_to_register, NULL);
}

static void InitEventLoop() {
  evthread_use_pthreads();
}

ADD_INITIALIZER("EventLoopInit", &InitEventLoop);

////////////////////////////////////////////////////////////////////////////////
// FakeEvent
////////////////////////////////////////////////////////////////////////////////

FakeEvent::FakeEvent(event_base* base)
    : event_(event_new(base, -1, 0, &FakeEvent::FiredCallback, this)) {
  CHECK(event_ != nullptr);
}

FakeEvent::~FakeEvent() {
  event_free(event_);
}

void FakeEvent::Add() {
  // libevent does not treat user events like "normal" events and so will exit
  // if the only remaining event is a user event (at least in version 2.0. This
  // is fixed in 2.1 but that is currently still in alpha). The workaround is
  // set a timeout. But we don't really want it to timeout so we set a timeout
  // for 20 years from now.
  static timeval forever = {20 * 365 * 24 * 60 * 60, 0};
  event_add(event_, &forever);
}

void FakeEvent::Remove() {
  // This fires the event which will cause the FiredCallback to be called. Since
  // the event isn't persistent that removes the event from the set of events
  // monitored by libevent.
  event_active(event_, 0, 0);
}

void FakeEvent::FiredCallback(int fd, short flags, void* this_ptr) {
}
