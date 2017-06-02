//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        This is the test harness that drives the TA1 client.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************

// Since most of the testing exercises the client, and not the server, this
// will serve as the "master" test harness component. It has a sequence of
// scripts that it runs. Most test capabilities of the client but some talk
// over the network to the server and ask the server to run a script. For
// example, the way the insert latency script gets run is for this test
// harness component to run a script. That script does nothing but contact the
// test harness component driving the server and ask it to run the server
// insert script. The script running here returns only when the server's
// script is complete.

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/assign/list_of.hpp>
#include <boost/shared_ptr.hpp>
#include <fstream>
#include <functional>
#include <string>
#include <ctime>

#include "client-sut-protocol-stack.h"
#include "common/periodic-real-time-logger.h"
#include "common/safe-file-stream.h"
#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/logging.h"
#include "common/statics.h"
#include "common/check.h"
#include "common/util.h"
#include "master-harness-network-listener.h"
#include "scripts/setup-client-harness-scripts.h"
#include "test-harness/common/spawn-sut.h"
#include "test-harness/common/log-file-generator.h"
#include "test-harness/common/scripts-from-file.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/test-script.h"

using boost::assign::list_of;
using std::string;
using std::vector;

namespace po = boost::program_options;

int main(int argc, char** argv) {
  Initialize();

  string debug_directory, test_script_path, test_log_path;
  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print help message")
      ("sut_path,p", po::value<string>(),
       "Path to the SUT executable")
      ("sut_args,a", po::value<string>(),
       "Arguments to pass to the SUT")
      ("listen_addr", po::value<string>(),
       "The IP address of the interface on which this should listen "
       "for connections from the server test harness. If blank "
       "this listens on all interfaces")
      ("listen_port", po::value<uint16_t>()->default_value(1234),
       "The port on which this should listen")
      ("test_script,t", po::value<string>(&test_script_path),
       "Path to the test script file indicating which commands to run. "
       "Other configutation files related to the test (e.g. query lists) are "
       "generally in the same directory")
      ("test_name,n", po::value<string>(),
       "Test name, which will be included in output logs.")
      ("test_log_dir", po::value<string>(&test_log_path),
       "The path to a directory where the test logs should be placed.")
      ("skip_network,s",
       "If given this will not wait for network connections. "
       "That limits the set of tests that can be run, but allows "
       "one to run tests that don't require the server harness.")
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
                                   ("test_name")("test_script")("test_log_dir");
  for (auto arg : req_args) {
    if (vm.count(arg) == 0) {
      LOG(FATAL) << "You must specify --" << arg;
    }
  }

  EventLoop event_loop;
  ClientSUTProtocolStack protocol_stack;

  SafeOFStream sut_stdout_log;
  SafeOFStream sut_stdin_log;

  LOG(INFO) << "Starting client SUT process";
  SUTRunningMonitor sut_running_monitor;

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
  LOG(INFO) << "Client SUT running.";

  event_loop.Start();

  HostPort listen_hp;
  if (vm.count("listen_addr") == 0) {
    listen_hp = HostPort::AnyAddress(vm["listen_port"].as<uint16_t>());
  } else {
    listen_hp = HostPort(vm["listen_addr"].as<string>().c_str(),
                         vm["listen_port"].as<uint16_t>());
  }

  MasterHarnessNetworkListener listener;
  listener.StartServer(&event_loop, listen_hp);

  MasterHarnessProtocolStack* network_stack = NULL;
  if (vm.count("skip_network") == 0) {
    LOG(INFO) << "Waiting for server test harness to connect.";
    listener.WaitForConnection();
    LOG(INFO) << "Server harness connected. Starting tests.";
    network_stack = listener.GetProtocolStack();
  } else {
    LOG(INFO) << "Not waiting for network connections. Tests that require "
        << "the server will fail.";
  }

  // Set up the set of available scripts, read the ones to execute from a file
  // and run them.
  ScriptsFromFile scripts_from_file;
  SetupClientHarnessScripts(
      &protocol_stack, network_stack, &sut_running_monitor, &scripts_from_file);

  CHECK(vm.count("test_script") > 0)
      << "Must supply the --test_script command line option.";
  SafeIFStream test_script_file(test_script_path.c_str());

  // We need a nice file-path manipulator library for C++, but for now...
  size_t dir_separator_idx = test_script_path.rfind('/');
  string test_script_dir;
  if (dir_separator_idx != string::npos) {
    // If it is == string::npos then the config file is in the current
    // directory so the path is empty which is what the default constructor
    // for string creates so we're good.
    DCHECK(dir_separator_idx + 1 < test_script_path.size());
    test_script_dir = test_script_path.substr(0, dir_separator_idx + 1);
    DCHECK(test_script_dir.at(test_script_dir.size() - 1) == '/');
  }

  vector<boost::shared_ptr<TestScript> > scripts_to_run;
  vector<GeneralLogger*> script_loggers;

  // Obtain the system time for the header lines in log files
  time_t rawtime = time(0);
  struct tm* timeinfo = localtime(&rawtime);
  char timebuffer[20];
  strftime(timebuffer, 20, "%Y-%m-%d %H:%M:%S", timeinfo);
  string timestring(timebuffer);
  // Obtain the current working directory for the header lines in log files
  char cwdbuffer[256];
  char* cwd = getcwd(cwdbuffer, 256);
  DCHECK(cwd != nullptr);
  string cwdstring(cwd);
  // Build the header lines
  vector<string> header_lines = 
    list_of(string(timestring + " " + vm["test_name"].as<string>()))
           ("Invoked from " + cwdstring)
           ("NOTE: ID x-y QID z = x-globalID, y-localID, z-resultsDBQueryID");
  FirstTokenRawTimeLogFileGenerator log_generator(
      vm["test_log_dir"].as<string>(), vm.count("unbuffered_debug") > 0,
      header_lines);
  scripts_from_file.TestsFromConfiguration(
      &test_script_file, test_script_dir, log_generator,
      &scripts_to_run, &script_loggers);

  LOG(INFO) << "Will run " << scripts_to_run.size() << " test scripts.";

  DCHECK(scripts_to_run.size() == script_loggers.size());
  for (size_t i = 0; i < scripts_to_run.size(); ++i) {
    LOG(INFO) << "Running test script";
    PeriodicRealTimeLogger pl(script_loggers[i],
        vm["timestamp_period"].as<unsigned int>());
    pl.Start();
    scripts_to_run[i]->Run();
    pl.Stop();
    script_loggers[i]->Log("END_OF_LOG");
    // Free the logger immediately so the file closes as we can score the
    // script.
    delete script_loggers[i];
    LOG(INFO) << "Script complete";
  }

  listener.StopListening();
  event_loop.ExitLoopAndWait();

  return 0;
}
