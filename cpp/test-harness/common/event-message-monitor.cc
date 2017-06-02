//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of EventMessageMonitor.
//*****************************************************************

#include "event-message-monitor.h"
#include "common/string-algo.h"
#include "common/knot.h"

using namespace std;

const char kEvent[] = "EVENTMSG";
const int kEventLen = strlen(kEvent);

EventMessageMonitor::~EventMessageMonitor() {
  for (auto pair : event_cb_map_) {
    RemoveCallback(pair.first);
  }
}

void EventMessageMonitor::OnProtocolStart(Knot line) {
  DCHECK(line.Equal(kEvent, kEventLen));
}

void EventMessageMonitor::RegisterCallback(int global_id, EventCallback eb) {
  DCHECK(eb != nullptr);
  MutexGuard l(data_tex_);
  DCHECK(event_cb_map_.find(global_id) == event_cb_map_.end());
  event_cb_map_.insert(make_pair(global_id, eb));
  LOG(DEBUG) << "Registered callback for command " << global_id;
}

EventMessageMonitor::EventCallback 
    EventMessageMonitor::GetCallback(int global_id) {
  MutexGuard l(data_tex_);
  DCHECK(event_cb_map_.find(global_id) != event_cb_map_.end());
  return event_cb_map_[global_id];
}

void EventMessageMonitor::RemoveCallback(int global_id) {
  MutexGuard l(data_tex_);
  DCHECK(event_cb_map_.find(global_id) != event_cb_map_.end());
  event_cb_map_.erase(global_id);
}

void EventMessageMonitor::LineReceived(Knot line) {
  LOG(DEBUG) << "Parsing EVENTMSG info: " << line;
  // Extract the event's command id
  Knot::iterator event_cmd_id_it = line.Find(' ');
  DCHECK(event_cmd_id_it != line.end());
  // Increment the iterator by 1, past the space character
  Knot event_cmd_id_knot = line.Split(++event_cmd_id_it);
  int event_cmd_id = ConvertString<int>(event_cmd_id_knot.ToString());
  LOG(DEBUG) << "Received event message for command " << event_cmd_id;

  // Extract the event id
  Knot::iterator event_id_it = line.Find(' ');
  int event_id = -1;
  if (event_id_it == line.end()) {
    event_id = ConvertString<int>(line.ToString());
    line.Clear();
  } else {
    // Increment the iterator by 1, past the space character
    Knot event_id_knot = line.Split(++event_id_it);
    event_id = ConvertString<int>(event_id_knot.ToString());
  }
  LOG(DEBUG) << "Received event message id " << event_id;

  // Call event callback
  EventCallback cb;
  {
    MutexGuard l(data_tex_);
    DCHECK(event_cb_map_.find(event_cmd_id) != event_cb_map_.end());
    cb = event_cb_map_.find(event_cmd_id)->second;
  }
  cb(event_cmd_id, event_id, line);

  // TODO(njhwang) currently there is no way to unregister events after RESULTS
  // are all received; this would be needed if events for a given command are
  // *not* free to occur for the lifetime of the SUT (i.e., because it's
  // expensive to maintain pointers to callbacks for every single command ID
  // forever)
  Done();
}

void EventMessageMonitor::RawReceived(Knot data) {
  LOG(FATAL) << "Event message monitor received raw data; "
             << "event message monitor should only receive line data";
}
