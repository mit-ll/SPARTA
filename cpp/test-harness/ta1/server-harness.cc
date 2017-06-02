//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        This is the test harness that drives the TA1 server. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************

// Since most of the tests exercies the client this serves as a slave to the
// test harness component driving the client. It connects to the client
// harness and simply waits for commands.

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/assign/list_of.hpp>
#include <boost/bind.hpp>
#include <chrono>
#include <memory>
#include <string>
#include <thread>

#include "server-sut-protocol-stack.h"

#include "baseline/common/numbered-command-receiver.h"
#include "common/periodic-real-time-logger.h"
#include "common/safe-file-stream.h"
#include "common/general-logger.h"
#include "common/network-client.h"
#include "common/event-loop.h"
#include "common/host-port.h"
#include "common/logging.h"
#include "common/statics.h"
#include "common/check.h"
#include "common/util.h"
#include "scripts/variable-delay-modify-argument-script.h"
#include "scripts/unloaded-modify-argument-script.h"
#include "scripts/verify-script.h"
#include "slave-network-stack.h"
#include "test-harness/common/root-mode-local-script.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/script-manager.h"
#include "test-harness/common/spawn-sut.h"

using boost::assign::list_of;
using std::string;
using std::vector;

namespace po = boost::program_options;

void SetupScripts(ServerSUTProtocolStack* sut_protocols,
                  SUTRunningMonitor* sut_monitor,
                  GeneralLogger* logger,
                  ScriptManager* script_manager) {
  script_manager->AddArgumentScript(
      "VariableDelayModifyArgumentScript",
      VariableDelayModifyFactory(
          sut_protocols->GetInsertCommand(),
          sut_protocols->GetUpdateCommand(),
          sut_protocols->GetDeleteCommand(),
          logger));
  script_manager->AddArgumentScript(
      "UnloadedModifyArgumentScript",
      UnloadedModifyArgumentFactory(
          sut_protocols->GetInsertCommand(),
          sut_protocols->GetUpdateCommand(),
          sut_protocols->GetDeleteCommand(),
          logger));

  script_manager->AddArgumentScript(
      "VerifyScript",
      VerifyScriptFactory(
          sut_protocols->GetVerifyCommand(), logger));

  script_manager->AddArgumentScript(
      "RootModeLocalScript",
      RootModeLocalScriptFactory(
          sut_protocols->GetRootModeCommandSender(), sut_monitor, logger));
}

int main(int argc, char** argv) {
  Initialize();

  string debug_directory, test_log_path;
  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print help message")
      ("sut_path,p", po::value<string>(),
       "Path to the SUT executable")
      ("sut_args,a", po::value<string>(),
       "Arguments to pass to the SUT")
      ("test_log", po::value<string>(&test_log_path),
       "The path to the file where the test logs should be placed. If "
       "not given logs will be written to stdout.")
      ("connect_addr", po::value<string>(),
       "The IP address of the test harness driving the client.")
      ("connect_port", po::value<uint16_t>()->default_value(1234),
       "The port on which the test harness driving the client is listening")
      ("test_name,n", po::value<string>(),
       "Test name, which will be included in output logs.")
      ("debug_dir,d", po::value<string>(&debug_directory),
       "If given, all data sent between the test harness and the SUT "
       "will be logged to files in the given directory")
      ("unbuffered_debug,u", "If set and --debug_dir is set the "
       "output files will be unbuffered. This allows for debugging "
       "even if test harness crashes, but it has an impact on performance.")
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

  // Display help on options
  if (vm.count("help")) {
    std::cout << desc << std::endl;
    exit(0);
  }

  // Set logging level
  if (vm.count("verbose") > 0) {
    Log::SetApplicationLogLevel(DEBUG);
  } else {
    Log::SetApplicationLogLevel(INFO);
  }

  // Validate command line options
  vector<string> req_args = list_of(string("sut_path"))("sut_args")
                                   ("connect_addr")("test_name");
  for (auto arg : req_args) {
    if (vm.count(arg) == 0) {
      LOG(FATAL) << "You must specify --" << arg;
    }
  }

  SUTRunningMonitor sut_running_monitor;
  EventLoop event_loop;
  ServerSUTProtocolStack protocol_stack;
  SafeOFStream sut_stdout_log;
  SafeOFStream sut_stdin_log;
  
  LOG(INFO) << "Starting server SUT process";
  // Setup function that will spawn the SUT and create valid pipes to the SUT's
  // stdin/out.
  auto pipe_fun = [&](int* sut_stdin, int* sut_stdout) {
    return SpawnAndConnectPipes(vm["sut_path"].as<string>(), 
                                vm["sut_args"].as<string>(), 
                                sut_stdin, sut_stdout);
  };
  SpawnSUT(pipe_fun, 
           debug_directory, vm.count("unbuffered_debug") > 0,
           &event_loop, &sut_stdout_log, &sut_stdin_log, &protocol_stack,
           std::bind(&SUTRunningMonitor::SUTShutdown, &sut_running_monitor));
  LOG(INFO) << "Server SUT running.";
  event_loop.Start();

  // Set up loggers
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
  // Obtain the system time for the log file header lines
  time_t rawtime = time(0);
  struct tm* timeinfo = localtime(&rawtime);
  char timebuffer[20];
  strftime(timebuffer, 20, "%Y-%m-%d %H:%M:%S", timeinfo);
  string timestring(timebuffer);
  // Obtain the current working directory for the log file header lines
  char cwdbuffer[256];
  char* cwd = getcwd(cwdbuffer, 256);
  DCHECK(cwd != nullptr);
  string cwdstring(cwd);
  // Build the header lines
  vector<string> header_lines = 
    list_of(string(timestring + " " + vm["test_name"].as<string>()))
           ("Invoked from " + cwdstring)
           ("NOTE: ID x MID y = x-globalID, y-resultsDBModificationID");
  // Write the header lines
  for (auto& header_line : header_lines) {
    logger->Log(header_line);
  }
  // Start the periodic system time stamping
  PeriodicRealTimeLogger pl(logger,
      vm["timestamp_period"].as<unsigned int>());
  pl.Start();

  ScriptManager script_manager;
  SetupScripts(&protocol_stack, &sut_running_monitor, logger, &script_manager);

  HostPort connect_hp(vm["connect_addr"].as<string>().c_str(),
                      vm["connect_port"].as<uint16_t>());

  ConnectionStatus cs;
  while (true) {
    NetworkClient network_client(&event_loop);
    cs = network_client.ConnectToServer(connect_hp);
    if (cs.success) {
      break;
    }
    LOG(INFO) << "Could not connect to the client harness. Will try again.";
    const int kNumWaitSeconds = 2;
    std::this_thread::sleep_for(std::chrono::seconds(kNumWaitSeconds));
  }
  LOG(INFO) << "Connection to " << connect_hp.ToString() << " successful";
  event_loop.RegisterEOFCallback(
      cs.connection->GetFileDescriptor(),
      [&](){ 
        LOG(INFO) << "Client harness disconnected. Exiting"; 
        pl.Stop();
        delete logger;
        test_log_file.close();
        exit(1); 
      });

  // Set up the protocol handler stack ending with a handler that can run
  // scripts. Then just wait on the event loop to finish.
  SlaveNetworkStack network_stack(cs.connection, &script_manager);

  sut_running_monitor.WaitForShutdown();
  LOG(INFO) << "SUT has shutdown. Exiting.";

  LOG(INFO) << "Waiting for all network commands to complete";
  network_stack.GetNumberedCommandReceiver()->WaitForAllCommands();
  LOG(INFO) << "All pending network commands done. Shutting down network "
      << "connection to the client harness";
  pl.Stop();
  cs.connection->Shutdown();
  event_loop.ExitLoopAndWait();
  delete logger;
  test_log_file.close();

  return 0;
}
