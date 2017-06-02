//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for ConnectToServer and
//                     EventLoop::ListenForConnections. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 Sep 2012   omd            Original Version
//*****************************************************************


// NOTE: unit tests that use network sockets, even to localhost, tend to be
// flaky. In this case that can't be avoided, but don't be too worried if these
// tests fail once in a blue moon.
//
// TODO(odain) We can probably make these tests a bit more robust. For example,
// instead of using a fixed port we can probably find a way to find the next
// available port so we don't get errors if our chosen port is in use.

#include "event-loop.h"
#include "line-raw-parser.h"
#include "network-client.h"
#include "network-server.h"

#include <boost/thread.hpp>
#include <vector>
#include <memory>

#define BOOST_TEST_MODULE NetworkingTest

#include "test-init.h"

using namespace std;

// A LineRawParseHandler that just keeps a vector of every line it receives.
class AppendHandler : public LineRawParseHandler {
 public:
  virtual void LineReceived(Knot data) {
    boost::lock_guard<boost::mutex> l(data_tex_);
    lines_.push_back(data);
    line_received_cond_.notify_all();
  }

  virtual void RawReceived(Knot data) {
    LOG(FATAL) << "Unexpected!";
  }

  void WaitForLineCount(int desired_count) {
    boost::unique_lock<boost::mutex> l(data_tex_);
    while (lines_.size() < static_cast<size_t>(desired_count)) {
      line_received_cond_.wait(l);
    }
  }

  std::vector<Knot> lines_;

 private:
  boost::mutex data_tex_;
  boost::condition_variable line_received_cond_;
};

BOOST_AUTO_TEST_CASE(ClientServerConnectionWorks) {
  // Two different event loops. One for the sever, one for the clients.
  EventLoop el_server, el_client;
  // Set up the server to listen on a port.
  const uint16_t kServerPort = 1234;
  // Passing an empty boost::function() to the constructor - we don't need a
  // callback when there are new connections.
  NetworkServer server(
      HostPort::AnyAddress(kServerPort), &el_server,
      NetworkServer::ConnectionCallback());
  NetworkClient client1(&el_client);
  NetworkClient client2(&el_client);
  el_server.Start();
  el_client.Start();
  LOG(DEBUG) << "Checkpoint 1";

  client1.InitiateServerConnection(HostPort("127.0.0.1", kServerPort));
  client2.InitiateServerConnection(HostPort("127.0.0.1", kServerPort));

  LOG(DEBUG) << "Checkpoint 1.4";
  server.BlockUntilNumConnections(1);
  LOG(DEBUG) << "Checkpoint 1.5";
  server.BlockUntilNumConnections(2);
  BOOST_REQUIRE_EQUAL(server.NumConnections(), 2);
  
  LOG(DEBUG) << "Checkpoint 2";
  ConnectionStatus cs1 = client1.WaitForConnection();
  ConnectionStatus cs2 = client2.WaitForConnection();
  BOOST_CHECK_EQUAL(cs1.success, true);
  BOOST_CHECK_EQUAL(cs2.success, true);

  // Now set up both connections so we know what the client and server received.
  AppendHandler* c1_h = new AppendHandler;
  LineRawParser c1_p(c1_h);
  AppendHandler* c2_h = new AppendHandler;
  LineRawParser c2_p(c2_h);

  LOG(DEBUG) << "Checkpoint 3";
  AppendHandler* s_from_c1_h = new AppendHandler;
  LineRawParser s_from_c1_p(s_from_c1_h);
  AppendHandler* s_from_c2_h = new AppendHandler;
  LineRawParser s_from_c2_p(s_from_c2_h);

  cs1.connection->RegisterDataCallback(
      boost::bind(&LineRawParser::DataReceived, &c1_p, _1));
  cs2.connection->RegisterDataCallback(
      boost::bind(&LineRawParser::DataReceived, &c2_p, _1));

  NetworkConnection* s_to_c1 = server.GetConnectionById(0);
  NetworkConnection* s_to_c2 = server.GetConnectionById(1);

  s_to_c1->RegisterDataCallback(
      boost::bind(&LineRawParser::DataReceived, &s_from_c1_p, _1));
  s_to_c2->RegisterDataCallback(
      boost::bind(&LineRawParser::DataReceived, &s_from_c2_p, _1));

  s_to_c1->GetWriteQueue()->Write(
      new Knot(new string("Server to client 1\n")));
  s_to_c2->GetWriteQueue()->Write(
      new Knot(new string("Server to client 2\n")));

  cs1.connection->GetWriteQueue()->Write(
      new Knot(new string("Client 1 to server.\n")));
  cs2.connection->GetWriteQueue()->Write(
      new Knot(new string("Client 2 to server.\n")));

  s_to_c1->GetWriteQueue()->Write(
      new Knot(new string("More Data for Client 1\n")));

  cs2.connection->GetWriteQueue()->Write(
      new Knot(new string("More Data from client 2\n")));

  // Wait until everything gets received.
  c1_h->WaitForLineCount(2);
  c2_h->WaitForLineCount(1);
  s_from_c1_h->WaitForLineCount(1);
  s_from_c2_h->WaitForLineCount(2);


  LOG(DEBUG) << "Shutting down";
  server.StopListening();
  s_to_c1->Shutdown();
  s_to_c2->Shutdown();

  el_server.ExitLoopAndWait();
  el_client.ExitLoopAndWait();

  BOOST_REQUIRE_EQUAL(c1_h->lines_.size(), 2);
  BOOST_CHECK_EQUAL(c1_h->lines_[0], "Server to client 1");
  BOOST_CHECK_EQUAL(c1_h->lines_[1], "More Data for Client 1");

  BOOST_REQUIRE_EQUAL(c2_h->lines_.size(), 1);
  BOOST_CHECK_EQUAL(c2_h->lines_[0], "Server to client 2");

  BOOST_REQUIRE_EQUAL(s_from_c1_h->lines_.size(), 1);
  BOOST_CHECK_EQUAL(s_from_c1_h->lines_[0], "Client 1 to server.");

  BOOST_REQUIRE_EQUAL(s_from_c2_h->lines_.size(), 2);
  BOOST_CHECK_EQUAL(s_from_c2_h->lines_[0], "Client 2 to server.");
  BOOST_CHECK_EQUAL(s_from_c2_h->lines_[1], "More Data from client 2");
}
