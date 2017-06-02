//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            ni24039
// Description:        This is the test harness that drives TA3 clients.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   njh            Tailored for TA3
//*****************************************************************

// This serves as a slave to the test harness component driving the clients. It
// connects to the master harness and simply waits for commands.

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <fstream>
#include <chrono>
#include <thread>

#include "common/periodic-real-time-logger.h"
#include "common/check.h"
#include "common/event-loop.h"
#include "common/safe-file-stream.h"
#include "common/general-logger.h"
#include "common/logging.h"
#include "common/statics.h"
#include "common/network-client.h"
#include "common/util.h"
#include "common/string-algo.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/script-manager.h"
#include "baseline/common/numbered-command-receiver.h"
#include "multi-client-sut-protocol-stack.h"
#include "scripts/setup-slave-harness-scripts.h"
#include "slave-harness-network-stack.h"

using std::string;
using std::vector;

namespace po = boost::program_options;

int main(int argc, char** argv) {
  Initialize();

  string debug_directory, test_log_path;
  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print help message")
      ("harness_id,i", po::value<string>(),
       "ID for this harness")
      ("num_suts,n", po::value<size_t>()->default_value(1),
       "Number of SUTs this harness will spawn")
      ("sut_path,p", po::value<string>(),
       "Path to the SUT executable")
      ("sut_args,a", po::value<string>()->default_value(""),
       "Arguments to pass to the SUT. If no ';' is found, these args will be "
       "passed to all spawned SUTs. Otherwise, there is expected to be N-1 "
       "';'s to create a total of N unique args strings to pass to each of "
       "the N spawned SUTs.")
      ("connect_addr", po::value<string>(),
       "The IP address of the master harness to which this harness will connect")
      ("connect_port", po::value<uint16_t>()->default_value(1234),
       "The master harness port to which this should connect")
      ("test_log", po::value<string>(&test_log_path),
       "The path to the file where the test logs should be placed.")
      ("debug_dir,d", po::value<string>(&debug_directory),
       "If given, all data sent between this harness and the SUTs "
       "will be logged to files in this directory")
      ("unbuffered_debug,u", "If set and --debug_dir is set the "
       "output files will be unbuffered. This allows for debugging "
       "even if this harness crashes, but it has an impact on performance.")
      ("verbose,v", "If set, will output all messages at DEBUG level and "
       "above. Otherwise, will output all messages at INFO level and above.")
      ("timestamp_period", po::value<unsigned int>()->default_value(60*5),
       "Interval in seconds with which to log system time in all logs");
  po::variables_map vm;

  try {
    po::store(po::parse_command_line(argc, argv, desc), vm);
  }
  catch (const boost::bad_any_cast &ex) {
    LOG(FATAL) << ex.what();
  }
  catch (const boost::program_options::invalid_option_value& ex) {
    LOG(FATAL) << ex.what();
  }


  po::notify(vm);

  if (vm.count("help")) {
    std::cout << desc << std::endl;
    exit(0);
  }

  // Validate command line options.
  CHECK(vm.count("harness_id")) << 
    "Must supply a harness ID that uniquely identifies this slave harness.";
  CHECK(vm.count("test_log")) << "Must specify an output test log.";
  CHECK(vm.count("sut_path")) << "Must supply a SUT path to spawn from.";
  CHECK(vm.count("connect_addr")) << 
    "Must supply a master harness IP address to connect to.";
  if (vm.count("verbose") > 0) {
    Log::SetApplicationLogLevel(DEBUG);
  } else {
    Log::SetApplicationLogLevel(INFO);
  }
  vector<string> sut_argsv = Split(vm["sut_args"].as<string>(), ';');
  if (sut_argsv.size() != 1) {
    CHECK(sut_argsv.size() == vm["num_suts"].as<size_t>())
      << "Must specify a single argument string to pass to all SUTs, or "
      << "a ';' delimited list of unique argument strings to pass to each "
      << "SUT. In the latter case, there must be N-1 ';' characters if there "
      << "are N SUTs.";
  }

  LOG(INFO) << "Starting slave harness (ID: " << 
               vm["harness_id"].as<string>() << ") with " <<
               vm["num_suts"].as<size_t>() << " SUTs";

  // Kick off event loop for I/O handling.
  vector<SUTRunningMonitor*> sut_monitors;
  for (size_t i = 0; i < vm["num_suts"].as<size_t>(); i++) {
    sut_monitors.push_back(new SUTRunningMonitor());
  }
  EventLoop event_loop;
  event_loop.Start();

  // Set up network connection to master harness.
  // Note that this establishes a network connection, but nothing is set up to
  // send/receive data over the connection yet.
  HostPort connect_hp(vm["connect_addr"].as<string>().c_str(), 
                      vm["connect_port"].as<uint16_t>());
  LOG(INFO) << "Connecting to " << connect_hp.ToString();
  ConnectionStatus cs;
  while (true) {
    NetworkClient network_client(&event_loop);
    cs = network_client.ConnectToServer(connect_hp);
    if (cs.success) {
      break;
    }
    LOG(INFO) << "Could not connect to the master harness. Trying again.";
    // TODO(njhwang) make this a parameter
    const int kNumWaitSeconds = 2;
    std::this_thread::sleep_for(std::chrono::seconds(kNumWaitSeconds));
  }
  LOG(INFO) << "Connected to " << connect_hp.ToString();
  LOG(DEBUG) << "NOTE: not receiving master harness commands yet";

  // Set up a network stack to handle communication with the master harness.
  // Note that still nothing is set up to receive data over the connection yet;
  // network_stack.Start() must be called before that can happen.
  ScriptManager script_manager;
  SlaveHarnessNetworkStack network_stack(vm["harness_id"].as<string>(), 
                                         vm["num_suts"].as<size_t>(), 
                                         cs.connection, &script_manager);

  // Set up test logging stream.
  std::ostream* log_stream;
  // Need to declare here so the ofstream doesn't go out of scope before the end
  // of the test.
  SafeOFStream test_log_file;
  if (test_log_path.empty()) {
    log_stream = &std::cout;
  } else {
    test_log_file.open(test_log_path.c_str());
    log_stream = &test_log_file;
  }
  OstreamRawTimeLogger* logger = 
    new OstreamRawTimeLogger(log_stream, false, 
                             vm.count("unbuffered_debug") > 0);
  PeriodicRealTimeLogger pl(logger,
      vm["timestamp_period"].as<unsigned int>());
  pl.Start();

  event_loop.RegisterEOFCallback(
      cs.connection->GetFileDescriptor(),
      [&](){ 
        // Close the log to flush its contents.
        LOG(FATAL) << "Master harness disconnected. " <<
                     "Flushing remaining data to log file";
        pl.Stop();
        delete logger;
        test_log_file.close();
        LOG(FATAL) << "Exiting slave harness."; 
      });

  LOG(INFO) << "Starting client SUT processes";
  // Setup function that will spawn the SUT and create valid pipes to the SUT's
  // stdin/out.
  auto spawn_fun = [&](int* sut_stdin, int* sut_stdout, string sut_args) {
    return SpawnAndConnectPipes(vm["sut_path"].as<string>(), 
                                sut_args, sut_stdin, sut_stdout);
  };
  // Spawn client SUT(s) and associated protocol stacks.
  MultiClientSUTProtocolStack protocol_stack(
      spawn_fun, debug_directory, vm.count("unbuffered_debug") > 0,
      &event_loop, vm["num_suts"].as<size_t>(), &network_stack, 
      sut_monitors, sut_argsv, logger);
  
  // Set up test scripts.
  SetupSlaveHarnessScripts(&protocol_stack, logger, &script_manager,
      sut_monitors);

  // Start slave harness network stack and allow it to process network data.
  network_stack.Start();
  LOG(DEBUG) << "NOTE: now receiving master harness commands";

  // Wait for commands to execute scripts until the event loop exits (i.e. via a
  // SHUTDOWN command).
  int shutdown_count = 0;
  for (auto item : sut_monitors) {
    item->WaitForShutdown();
    LOG(INFO) << "Detected client SUT #" << shutdown_count++ << " shutdown";
  }

  LOG(DEBUG) << "All SUTs shutdown. " <<
               "Waiting for all network commands to complete";
  network_stack.GetNumberedCommandReceiver()->WaitForAllCommands();
  pl.Stop();

  LOG(DEBUG) << "Shutting down connection to master harness";
  cs.connection->Shutdown();
  LOG(DEBUG) << "Waiting for remaining slave harness events to complete";
  event_loop.ExitLoopAndWait();
  LOG(DEBUG) << "Waiting for spawned client SUT processes to terminate";
  protocol_stack.WaitUntilAllSUTsDie();
  // Close the log to flush its contents.
  LOG(DEBUG) << "Flushing remaining data to log file";
  delete logger;
  test_log_file.close();
  LOG(INFO) << "Slave harness successfully shutdown";

  return 0;
}
