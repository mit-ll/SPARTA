//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of MasterHarnessNetworkListener
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#include "master-harness-network-listener.h"

using namespace std;

////////////////////////////////////////////////////////////////////////////////
// MasterHarnessProtocolStack
////////////////////////////////////////////////////////////////////////////////

MasterHarnessProtocolStack::MasterHarnessProtocolStack(
    NetworkConnection* connection)
    : NetworkProtocolStack(connection),
      run_script_command_(new THRunScriptCommand(GetNumberedCommandSender())) {
}

// Note that we did not make a command class for HARNESS_INFO.
// NetworkProtocolStacks use MultiNumberedCommandSenders, and we therefore
// cannot have a HarnessInfoCommand that is a subclass of
// GenericNumberedCommand, since GenericNumberedCommands require
// NumberedCommandSenders. It would be just as much code to create a new command
// class for HarnessInfoCommand, and so we just include it here.
string MasterHarnessProtocolStack::GetSlaveHarnessInfo() {
  // Send HARNESS_INFO request.
  Knot command_data(new string("HARNESS_INFO\n"));
  int to_discard;
  NumberedCommandSender::ResultsFuture future;
  LOG(DEBUG) << "Master harness sending HARNESS_INFO command";
  GetNumberedCommandSender()->SendCommand(
      command_data,
      boost::bind(&MasterHarnessProtocolStack::SlaveHarnessInfoReceived, 
                  this, _1, future), 
      &to_discard);
  
  // Return the response to the caller.
  LOG(DEBUG) << "Master harness waiting for HARNESS_INFO response";
  LineRawData<Knot> results = future.Value()->results_received;
  LOG(DEBUG) << "Master harness received HARNESS_INFO response";
  DCHECK(results.Size() == 1);
  DCHECK(!results.IsRaw(0));
  return results.Get(0).ToString();
}

void MasterHarnessProtocolStack::SlaveHarnessInfoReceived( 
    NumberedCommandSender::SharedResults results,
    NumberedCommandSender::ResultsFuture future) {
  future.Fire(results);
  GetNumberedCommandSender()->RemoveCallback(results->command_id);
}

////////////////////////////////////////////////////////////////////////////////
// MasterHarnessNetworkListener
////////////////////////////////////////////////////////////////////////////////

MasterHarnessNetworkListener::MasterHarnessNetworkListener() : 
  event_loop_(nullptr) {}

void MasterHarnessNetworkListener::StartServer(EventLoop* event_loop,
                                               HostPort listen_addr_port) {
  CHECK(event_loop_ == nullptr);
  CHECK(network_server_.get() == nullptr);
  event_loop_ = event_loop;

  network_server_.reset(
      new NetworkServer(
          listen_addr_port, event_loop_,
          boost::bind(&MasterHarnessNetworkListener::ConnectionMade,
                      this, _1, _2)));
}

void MasterHarnessNetworkListener::ShutdownServer() {
  network_server_->StopListening(); 
}

void MasterHarnessNetworkListener::ConnectionMade(
    size_t conn_id, NetworkConnection* conn) {
  boost::lock_guard<boost::mutex> l(data_tex_);
  // Create a new protocol stack for each connection that is made. These will
  // later be mapped to harness/SUT IDs when UpdateNetworkMap() is called.
  MHPSPtr mh_protocols = new MasterHarnessProtocolStack(conn);
  protocol_stacks_.push_back(mh_protocols);
}

void MasterHarnessNetworkListener::BlockUntilNumConnections(size_t num_conn) {
  network_server_->BlockUntilNumConnections(num_conn);
}

size_t MasterHarnessNetworkListener::GetNumClientSUTs() {
  boost::lock_guard<boost::mutex> l(data_tex_);
  // Sum up SUT ID counts from each vector in harness_sut_map_.
  size_t total = 0;
  for (auto item : harness_sut_map_) {
    total += item.second->size();
  }
  return total;
}

size_t MasterHarnessNetworkListener::GetNumSlaveHarnesses() {
  boost::lock_guard<boost::mutex> l(data_tex_);
  return protocol_stacks_.size();
}

void MasterHarnessNetworkListener::UpdateNetworkMap() {
  boost::lock_guard<boost::mutex> l(data_tex_);
  size_t sut_id = 0;
  // Clear all maps; this will create a new mapping each time it is called.
  sut_ps_map_.clear();
  harness_ps_map_.clear();
  sut_harness_map_.clear();
  for (auto item : harness_sut_map_) {
    delete item.second;
  }
  harness_sut_map_.clear();

  // Iterate over each existing protocol stack and request its harness
  // information.
  for (vector<MHPSPtr>::iterator it = protocol_stacks_.begin();
       it != protocol_stacks_.end();
       it++) {
    string harness_info = (*it)->GetSlaveHarnessInfo();

    // Harness information will be composed of the harness ID and number of SUTs
    // it is driving, separated by a space.
    vector<string> parts = Split(harness_info, ' ');
    DCHECK(parts.size() == 2);
    string harness_id = parts[0];
    size_t num_suts = atoi(parts[1].c_str());

    // Update data structures with new mapping information.
    DCHECK(harness_ps_map_.find(harness_id) == harness_ps_map_.end());
    harness_ids_.push_back(harness_id);
    harness_ps_map_.insert(make_pair(harness_id, *it));
    vector<size_t>* harness_suts = new vector<size_t>();
    for (size_t i = 0; i < num_suts; i++) {
      sut_ps_map_.insert(make_pair(sut_id, *it));
      sut_harness_map_.insert(make_pair(sut_id, harness_id));
      harness_suts->push_back(sut_id);
      ++sut_id;
    }
    harness_sut_map_.insert(make_pair(harness_id, harness_suts));
  }
}

MasterHarnessNetworkListener::MHPSPtr 
    MasterHarnessNetworkListener::GetProtocolStack(string harness_id) {
  boost::lock_guard<boost::mutex> l(data_tex_);
  DCHECK(harness_ps_map_.find(harness_id) != harness_ps_map_.end());
  return harness_ps_map_[harness_id];
}

MasterHarnessNetworkListener::MHPSPtr 
    MasterHarnessNetworkListener::GetProtocolStack(size_t sut_id) {
  boost::lock_guard<boost::mutex> l(data_tex_);
  DCHECK(sut_ps_map_.find(sut_id) != sut_ps_map_.end());
  return sut_ps_map_[sut_id];
}

vector<size_t>* MasterHarnessNetworkListener::GetClientSUTIDs(string harness_id) {
  boost::lock_guard<boost::mutex> l(data_tex_);
  DCHECK(harness_sut_map_.find(harness_id) != harness_sut_map_.end());
  return harness_sut_map_[harness_id];
}

string MasterHarnessNetworkListener::GetSlaveHarnessID(size_t sut_id) {
  boost::lock_guard<boost::mutex> l(data_tex_);
  DCHECK(sut_harness_map_.find(sut_id) != sut_harness_map_.end());
  return sut_harness_map_[sut_id];
}

vector<string>* MasterHarnessNetworkListener::GetAllSlaveHarnessIDs() {
  boost::lock_guard<boost::mutex> l(data_tex_);
  return &harness_ids_;
}
