//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        This is the test harness that drives the TA3 server. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

// This will serve as the "master" test harness component. It runs a test script
// specified by an input configuration file. Scripts typically first wait for
// the desired number of network connections to other slave harnesses, confirms
// their identities, then asks each slave harness to run certain scripts to tet
// the capabilities of client SUTs while simultaneously instructing the server
// SUT to publish certain data. The script running here returns only when all
// other slave scripts have completed.

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/shared_ptr.hpp>
#include <fstream>
#include <string>

#include "master-harness-network-listener.h"
#include "test-harness/common/spawn-sut.h"
#include "server-sut-protocol-stack.h"
#include "scripts/setup-master-harness-scripts.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/log-file-generator.h"
#include "test-harness/common/scripts-from-file.h"
#include "test-harness/common/test-script.h"
#include "common/periodic-real-time-logger.h"
#include "common/safe-file-stream.h"
#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/logging.h"
#include "common/statics.h"
#include "common/check.h"
#include "common/util.h"

using std::string;
using std::vector;

namespace po = boost::program_options;

int main(int argc, char** argv) {
  Initialize();

  string debug_directory, config_file_path, test_log_path;
  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print help message")
      ("sut_path,p", po::value<string>(),
       "Path to the SUT executable")
      ("sut_args,a", po::value<string>()->default_value(""),
       "Arguments to pass to the SUT")
      ("test_log_dir", po::value<string>(&test_log_path),
       "The path to the directory where the test logs should be placed.")
      ("listen_addr", po::value<string>(),
       "The IP address of the interface on which this should listen "
       "for connections from the server test harness. If blank, "
       "this listens on all interfaces")
      ("listen_port", po::value<uint16_t>()->default_value(1234),
       "The port on which this should listen")
      ("config_file,c", po::value<string>(&config_file_path),
       "Path to the configuration file indicating which tests to run. "
       "Other configutation files (e.g. publication lists) generally "
       "need to be in the same directory")
      ("debug_dir,d", po::value<string>(&debug_directory),
       "If given, all data sent between the test harness and the SUT "
       "will be logged to files in the given directory. Note that this "
       "directory must already exist.")
      ("unbuffered_debug,u", "If set and --debug_dir is set, the "
       "output debug files will be unbuffered. This allows for debugging "
       "even if this test harness crashes, but it has an impact on "
       "performance.")
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
  CHECK(vm.count("sut_path")) << "Must supply a server SUT path to spawn from.";
  CHECK(vm.count("test_log_dir")) << "Must specify an output test log directory.";
  CHECK(vm.count("config_file"))
      << "Must supply the --config_file command line option.";
  if (vm.count("verbose") > 0) {
    Log::SetApplicationLogLevel(DEBUG);
  } else {
    Log::SetApplicationLogLevel(INFO);
  }

  LOG(INFO) << "Starting master harness";
  EventLoop event_loop;
  SUTRunningMonitor sut_monitor;
  // Protocol stack that will communicate with the server SUT via stdin/out.
  ServerSUTProtocolStack protocol_stack;

  LOG(INFO) << "Starting server SUT process";
  std::ofstream sut_stdout_log;
  std::ofstream sut_stdin_log;
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
           std::bind(&SUTRunningMonitor::SUTShutdown, &sut_monitor));

  event_loop.Start();

  LOG(INFO) << "Opening network server connection";
  HostPort listen_hp;
  if (vm.count("listen_addr") == 0) {
    listen_hp = HostPort::AnyAddress(vm["listen_port"].as<uint16_t>());
  } else {
    listen_hp = HostPort(vm["listen_addr"].as<string>().c_str(),
                         vm["listen_port"].as<uint16_t>());
  }
  // Listener that hosts the network server and handles network communication
  // with slave harnesses.
  MasterHarnessNetworkListener listener;
  listener.StartServer(&event_loop, listen_hp);

  // Set up the set of available scripts.
  ScriptsFromFile scripts_from_file;
  FirstTokenRawTimeLogFileGenerator log_generator(
      vm["test_log_dir"].as<string>(), vm.count("unbuffered_debug") > 0);
  SetupMasterHarnessScripts(
      &protocol_stack, &listener, &scripts_from_file, &sut_monitor,
      &log_generator, vm["timestamp_period"].as<unsigned int>());
  
  // Read the scripts to execute from the provided configuration file.
  SafeIFStream script_config_file(config_file_path.c_str());
  // TODO(njhwang) we need a nice file-path manipulator library for C++, but for
  // now...
  size_t dir_separator_idx = config_file_path.rfind('/');
  string config_file_dir;
  if (dir_separator_idx != string::npos) {
    // If it is == string::npos then the config file is in the current directory
    // so the path is empty which is what the default constructor for string
    // creates so we're good.
    DCHECK(dir_separator_idx + 1 < config_file_path.size());
    config_file_dir = config_file_path.substr(0, dir_separator_idx + 1);
    DCHECK(config_file_dir.at(config_file_dir.size() - 1) == '/');
  }

  vector<boost::shared_ptr<TestScript> > scripts_to_run;
  vector<GeneralLogger*> script_loggers;

  scripts_from_file.TestsFromConfiguration(&script_config_file,
                                           config_file_dir,
                                           log_generator,
                                           &scripts_to_run,
                                           &script_loggers);

  // Run test scripts. Note that the first script run should generally be
  // UpdateNetworkMap script, which will block until a desired number of clients
  // have been spawned. The second script should generally be
  // WaitUntilAllClientsReady, which will block until all spawned clients have
  // emitted their first READY signal (which presumably indicates that they are
  // all connected to the server).
  LOG(INFO) << "Master harness will run " << scripts_to_run.size() 
            << " test scripts.";
  vector<boost::shared_ptr<TestScript> >::iterator script_it;
  DCHECK(scripts_to_run.size() == script_loggers.size());
  for (size_t i = 0; i < scripts_to_run.size(); ++i) {
    LOG(INFO) << "Starting test script #" << i;
    PeriodicRealTimeLogger pl(script_loggers[i],
        vm["timestamp_period"].as<unsigned int>());
    pl.Start();
    scripts_to_run[i]->Run();
    pl.Stop();
    // Free the logger immediately so the file closes and we can score the
    // script.
    delete script_loggers[i];
    LOG(INFO) << "Completed test script #" << i;
  }

  // Wait for the event loop to exit (i.e. via a SHUTDOWN command).
  sut_monitor.WaitForShutdown();
  LOG(INFO) << "Detected server SUT shut down";
  LOG(DEBUG) << "Shutting down server connection";
  listener.ShutdownServer();
  LOG(DEBUG) << "Waiting for remaining master harness events to complete";
  event_loop.ExitLoopAndWait();
  LOG(DEBUG) << "Waiting for server SUT process to terminate";
  protocol_stack.WaitUntilSUTDies();
  LOG(INFO) << "Master harness successfully shut down";

  return 0;
}
