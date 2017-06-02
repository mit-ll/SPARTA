//*****************************************************************
// Copyright 2012 BASE Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Main executable to start the TA2 test harness 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   yang           Original Version
// 21 Jan 2013   yang           Changed std::fstreams to SafeFStreams
//******************************************************************

#include <string>
#include <vector>
#include <fstream>

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/assign/list_of.hpp>

#include "common/logging.h"
#include "common/util.h"
#include "common/check.h"
#include "common/statics.h"
#include "common/safe-file-stream.h"
#include "test-harness/ta2/test-script.h"

using std::string;
using std::ofstream;
using boost::assign::list_of;

namespace po = boost::program_options;

#define PERF_IBM2 "IBM2"
#define PERF_BASE  "BASE"

bool checkFileExists(const std::string& filename) {
  std::ifstream file(filename);
  if (!file) {
    // Can't open file
    return false;
  }
  
  file.close();
  return true;
}

std::string checkLogFileDir(const std::string& test_log_dir) {
  // make sure the directory name ends in '/'

  if (test_log_dir.empty()) {
    LOG(FATAL) << "--test_log_dir cannot be an empty string";
  }
  char lastChar = *test_log_dir.rbegin();
  std::string delimiter = "";
  if (lastChar != '/')
    delimiter =  "/";
  std::string dirname = test_log_dir + delimiter;
  return dirname;
}

std::string getUniqueLogFilename(const std::string& test_log_dir, 
				 const std::string& test_name) {
  std::string file_template = test_log_dir + test_name +  "-XXXXXX";

  // Ok the ugly part starts here. You have to pass a char* to mkstemp,
  // so use strndup to malloc space.
  char* unique_filename = strndup(file_template.data(), file_template.size());
  int file = mkstemp(unique_filename);
  
  // Copy the new unique filename into to string that we can return
  std::string filename(unique_filename);

  // It gets uglier, as mkstemp actually opened the file, so we must close it  
 close(file);

  // do not forget to delete the space malloc allocated
  free(unique_filename);

  return filename;
}


int main(int argc, char** argv) {
  Initialize();
  string server, client, result, recovery, performer;
  string test_log_dir, test_script, test_name;

  string performer_option_help(string("Performer should be either ") + 
			       PERF_IBM2 + " or " + PERF_BASE);

  po::options_description desc("Options");
  desc.add_options()
    ("help,h", "print help message")
    ("performer,p", po::value<string>(&performer), 
     performer_option_help.c_str())
    ("server,s", po::value<string>(&server), 
     "Path to server executable")
    ("server_args,a", po::value<string>()->default_value(""),
     "Arguments to pass to the SUT server")
    ("client_args,b", po::value<string>()->default_value(""),
     "Arguments to pass to the SUT client")
    ("client,c", po::value<string>(&client), 
     "path to client executable")
    ("debug,d", po::value<string>(), "debug mode. The stdin and stdout of "
     "client and server will be captured to log files. If 'u' is specified, "
     "the logs will be unbuffered.")
    ("recovery,x",  po::value<string>(&recovery), 
     "Resumes a test script at the most recent crash, as "
     "indicated by the status file. Specify the name of the previous "
     "log file so that it can append where it left off. It will expect it "
     "in the test_log_dir, so just specify the name of the log file. "
     "For example: recovery=01_oneofeach_small_k80-tXdq6b")
    ("test_log_dir,l", po::value<string>(&test_log_dir),
     "The path to a directory where the test logs should be placed. "
     "This directory must exist.")
    ("test_script,t", po::value<string>(&test_script),
     "Path to the test script file indicating which commands to run. "
     "For example: foo/bar/test0001.ts")
    ("test_name,n", po::value<string>(&test_name),
     "Test name, which will be included in output logs.");
  
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

  // Validate command line options
  std::vector<string> req_args = list_of("server")("client")
    ("test_log_dir")("test_script")("test_name")("performer");
  for (auto arg : req_args) {
    if (vm.count(arg) == 0) {
      LOG(FATAL) << "You must specify --" << arg;
    }
  }
  test_log_dir = checkLogFileDir(test_log_dir);

  if (performer != PERF_IBM2 && performer != PERF_BASE) {
    LOG(FATAL) << "Invalid performer, the --performer option expects "
	       << "either " << PERF_IBM2 << " or " << PERF_BASE;
  }

  // Open the log file
  SafeOFStream* log;
  if (vm.count("recovery")) {
    // On recovery, append to the existing log file
    std::string log_file = test_log_dir + recovery;
    if (!checkFileExists(log_file)) {
      LOG(FATAL) << "The recovery log file " << log_file << " does not exist";
    }
    if (recovery.find(test_name) == std::string::npos) {
      LOG(WARNING) << "The recovery log file specified: " << recovery 
		   << " might not be for the test specified: " << test_name;
    }
    log = new SafeOFStream(log_file.c_str(), std::ios_base::app);
  }
  else {
    // Create a unique log file name from test_name
    std::string log_file = getUniqueLogFilename(test_log_dir, test_name);
    log = new SafeOFStream(log_file.c_str());
  }

  // Obtain the system time for the header lines in log files
  string timestring = GetCurrentTime();

  // Obtain the current working directory for the header lines in log files
  char cwdbuffer[256];
  getcwd(cwdbuffer, 256);
  string cwdstring(cwdbuffer);

  *log << "PERFORMER: " << performer << std::endl;
  *log << "TEST: " << test_name << " " << test_script << std::endl;
  *log << "TIME: " << timestring << std::endl;
  *log << "Invoked from " << cwdstring << std::endl;

  TestScript script(log);
  script.SpawnClient(client, vm["client_args"].as<string>());
  script.SpawnServer(server, vm["server_args"].as<string>());
  script.RegisterHandler(TestScript::KEY_DELIM, new KeyMessageHandler(log));
  script.RegisterHandler(
      TestScript::CIRCUIT_DELIM, new CircuitMessageHandler(log));
  script.RegisterHandler(TestScript::INPUT_DELIM,
                         new InputMessageHandler(log));
  script.InitHandlers();

  if (vm.count("debug")) {
    if (vm["debug"].as<string>() == "u") {
      script.SetDebugLogStream(false);
    } else {
      script.SetDebugLogStream(true);
    }
  }
  if (vm.count("recovery")) {
    *log << "RECOVERY" << std::endl;
    script.Resume(test_script);
  } else {
    script.Execute(test_script);
  }
}
