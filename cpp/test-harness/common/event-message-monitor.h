//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        For handling event messages.
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_EVENT_MESSAGE_MONITOR_H_
#define CPP_TEST_HARNESS_COMMON_EVENT_MESSAGE_MONITOR_H_

#include <thread>

#include "common/protocol-extension-manager.h"

class Knot;

/// Looks for event messages in the SUT's stdout. Upon reception of an event
/// message, if a callback was registered for the associated global command ID,
/// that callback is called. Callbacks are saved for each global command ID,
/// since it's theoretically possible for events to be reported for a global
/// command ID that has already returned results.
class EventMessageMonitor : public ProtocolExtension {
 public:
  EventMessageMonitor() {}
  virtual ~EventMessageMonitor();

  virtual void OnProtocolStart(Knot start_line);
  virtual void LineReceived(Knot line);
  virtual void RawReceived(Knot data); 

  typedef std::function<void (int, int, Knot)> EventCallback;
  void RegisterCallback(int global_id, EventCallback eb);
  EventCallback GetCallback(int global_id);
  void RemoveCallback(int global_id);

 private:
  std::mutex data_tex_;
  std::map<int, EventCallback > event_cb_map_;
};

#endif
