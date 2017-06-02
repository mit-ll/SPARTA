//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Class that manages a stack of multiple protocol parsers
//                     needed to control multiple client SUTs from a single test
//                     harness.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   njh            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_MULTI_CLIENT_SUT_PROTOCOL_STACK_H_
#define CPP_TEST_HARNESS_TA3_MULTI_CLIENT_SUT_PROTOCOL_STACK_H_

#include <functional>
#include <string>
#include <thread>
#include <vector>
#include <mutex>

class SlaveHarnessNetworkStack;
class ClientSUTProtocolStack;
class SUTRunningMonitor;
class GeneralLogger;
class EventLoop;

class MultiClientSUTProtocolStack {
 public:
  /// Constructor requires all the arguments required for the SpawnSUT function,
  /// as well as the number of SUTs to spawn. This constructor will spawn
  /// num_suts SUTs with identical parameters, each with their own protocol stack
  /// and logging output.
  MultiClientSUTProtocolStack(
    std::function<int(int*, int*, std::string)> spawn_fun,
    const std::string& debug_directory, bool unbuffered,
    EventLoop* event_loop, size_t num_suts, 
    SlaveHarnessNetworkStack* network_stack, 
    std::vector<SUTRunningMonitor*> sut_monitors, 
    std::vector<std::string> sut_argsv, GeneralLogger* logger);

  virtual ~MultiClientSUTProtocolStack();
  
  /// Waits until all protocol stacks have received a READY from their respective
  /// SUTs. This is primarily used to simplify the test start up sequence.  Since
  /// we did not request performers to implement a client CONNECTION message that
  /// signifies an established connection with their server/third-parties, we
  /// must instead detect the first READY signal for each client SUT at the
  /// beginning of the test, with the assumption that the first READY signal
  /// means that the client SUT has established all connectivity it needs to
  /// function and that it is ready to receive commands from the slave harness.
  /// Care should be taken to make sure that this is called at the appropriate
  /// time to ensure that the master harness does not command the server to
  /// publish anything before all the clients are ready.
  void WaitUntilAllReady();

  void WaitUntilAllSUTsDie();

  /// Fetches the protocol stack for the provided SUT ID.
  ClientSUTProtocolStack* GetProtocolStack(size_t sut_id);

  size_t GetNumClientSUTs();

 private:
  /// Protects the data structures below.
  std::mutex data_tex_;
  /// Each SUT will be assigned an ID from [0, num_suts).
  /// sut_pstacks_ effectively maps a SUT ID to its corresponding protocol stack.
  std::vector<ClientSUTProtocolStack*> sut_pstacks_;
  /// The following vectors are only used to save pointers to logging streams
  /// that need to be properly released upon exit. 
  std::vector<std::ofstream*> sut_stdin_logs_;
  std::vector<std::ofstream*> sut_stdout_logs_;
};

#endif
