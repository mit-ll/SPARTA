//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Base class for WriteEventLoop and ReadEventLoop 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_EVENT_LOOP_BASE_H_
#define CPP_COMMON_EVENT_LOOP_BASE_H_

#include <boost/thread.hpp>
#include <event2/event.h>
#include <memory>
#include <string>
#include <vector>

class EventLoop;
class WriteQueue;

/// libevent's event loop will exit as soon as there are no more active events
/// (at least in libevent 2.0. 2.1 fixes this but it's still alpha). However, we
/// sometimes want to keep the loop running with no events (e.g. all file handles
/// are currently writeable but future writes might be too big and require us to
/// register an event to find out when the file is writeable again). We therefore
/// register fake events with the loop so that EventLoopBase::RunTheLoop exits
/// only when we're sure all the work has been completed. There is some subtlety
/// with doing this right so we hide the details in this class. To use:
///
/// 1) Instantiate a FakeEvent
/// 2) When you have some work and you want to be sure the event loop won't exit
///    call Add().
/// 3) When the work is complete and the event loop can safely exit call
///    Remove().
///
/// It is safe to make as may Add/Remove pair calls as desired.
class FakeEvent {
 public:
  /// Construct a fake event for use with the given event_base.
  FakeEvent(event_base* base);
  /// Make sure to free the FakeEvent *before* you free the event_base that was
  /// passed to the constructor.
  virtual ~FakeEvent();

  void Add();
  void Remove();

 private:
  /// If a fake event is the last event monitored by an event loop and you call
  /// event_del on it the loop does *not* exit. Instead you have to fire the
  /// event. However, we don't actually care about the fired event since it's
  /// fake. This is thus a silly callback that does nothing. The parameters are
  /// as required by libevent's callbacks.
  static void FiredCallback(int fd, short flags, void* this_ptr);

  event* event_;
};

/// Both ReadEventLoop and WriteEventLoop inherit from this. This contains much
/// of the basic functionalty that takes care of thread safe event counting, loop
/// start and shutdown, etc.
class EventLoopBase {
 public:
  EventLoopBase();
  /// IMPORTANT: subclasses should call ExitLoopAndWait() in their destructors or
  /// otherwise ensure that the event loop has completed and exited.  This
  /// destructor assumes the loop has already been stopped.
  virtual ~EventLoopBase();

  /// Start the event loop in a seprate thread and return immediately.
  void Start();

  /// Tells the event loop to exit as soon as possible. Note that is is OK to
  /// call this more than once (though subsequent calls will have no effect).
  void ExitLoop();

  /// This blocks until the event loop is done. This should only be called after
  /// ExitLoop has been called.
  virtual void WaitForExit();

  /// Convenience method that calls ExitLoop() and then WaitForExit().
  void ExitLoopAndWait() {
    ExitLoop();
    WaitForExit();
  }

 protected:
  friend class EventLoop;
  /// This registers an event to be watched by libevent.
  void RegisterEvent(event* event_to_register);

  event_base* GetEventBase() {
    return event_base_;
  }

  boost::thread::id GetEventLoopThreadId() {
    return event_loop_thread_->get_id();
  }

 private:
  /// This is the main event loop. It is called by Start() in a new thread.
  void RunTheLoop();

  /// The thread that runs libevent's event loop when Start() is called.
  std::unique_ptr<boost::thread> event_loop_thread_;

  struct event_base* event_base_;
 
  /// The event_base_dispatch loop will exit when there are no more registered
  /// events. However, we don't want to shut down the event_loop_thread_ at that
  /// point as we may later add more events. This is quite common when using
  /// EventLoop to write to a file; If we have nothing to write we're not
  /// monitoring the file handle, but we might have something to write later.
  /// Thus we add this fake event that only fires when the user calls ExitLoop().
  std::unique_ptr<FakeEvent> master_event_;
};

#endif
