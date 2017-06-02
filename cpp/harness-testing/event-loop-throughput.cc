//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A version that uses our new EventLoop infrastructure. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Jul 2012   omd            Original Version
//*****************************************************************

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/thread.hpp>
#include <string>

#include "common/check.h"
#include "common/logging.h"
#include "common/statics.h"
#include "common/timer.h"
#include "common/util.h"
#include "test-harness/common/ready-monitor.h"

using namespace std;
namespace po = boost::program_options;

// This uses the minimal amount of EventLoop and ReadyMonitor stuff to
// performance test these components using the simple GO/READY protocol that
// silly-client follows. The idea is to quickly test if the framework we're
// building has good enough performance.

// Create a silly DATA handler that just discards everything.
class DataExtension : public ProtocolExtension {
 public:
  DataExtension(int num_data_expected) : num_data_received_(0),
    num_data_expected_(num_data_expected) {
  }

  virtual void LineReceived(Knot data) {
    if (data == "ENDDATA") {
      {
        boost::lock_guard<boost::mutex> l(received_count_tex_);
        ++num_data_received_;
        if (num_data_received_ >= num_data_expected_) {
          expected_number_received_.notify_all();
        }
      }
      Done();
    }
  }

  void WaitForAllReceived() {
    boost::unique_lock<boost::mutex> lock(received_count_tex_);
    while (num_data_received_ < num_data_expected_) {
      expected_number_received_.wait(lock);
    }
  }
 private:
  int num_data_received_;
  int num_data_expected_;

  boost::mutex received_count_tex_;
  boost::condition_variable expected_number_received_;
};

int main(int argc, char** argv) {
  Initialize();
  // Disable debug logging.
  Log::SetApplicationLogLevel(INFO);

  string executable, args;
  int num_trials;
  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print help message")
      ("executable,e", po::value<string>(&executable),
       "Path to the executable to run")
      ("args,a", po::value<string>(&args),
       "Command line arguments to pass to executable")
      ("num_trials,n", po::value<int>(&num_trials)->default_value(10000),
       "The number of iterations to do");

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
    cout << desc << endl;
    exit(0);
  }

  CHECK(executable.size() > 0);
  int process_stdout_h, process_stdin_h;

  SpawnAndConnectPipes(
      executable, args, &process_stdin_h, &process_stdout_h);

  // Set up our processing stack (event loop, ProtocolExtensionManager,
  // ReadyMonitor, etc.)
  EventLoop event_loop;
  ProtocolExtensionManager* manager = new ProtocolExtensionManager;
  ReadyMonitor* ready_monitor = new ReadyMonitor(
      event_loop.GetWriteQueue(process_stdin_h));
  manager->AddHandler("READY", ready_monitor);
  DataExtension* data_extension = new DataExtension(num_trials);
  manager->AddHandler("DATA", data_extension);

  LineRawParser parser(manager);
  event_loop.RegisterFileDataCallback(
      process_stdout_h,
      boost::bind(&LineRawParser::DataReceived, &parser, _1));

  event_loop.Start();

  ready_monitor->WaitUntilReady();
  Timer timer;
  timer.Start();
  for (int i = 0; i < num_trials; ++i) {
    ready_monitor->ScheduleSend(new Knot(new string("GO\n")));
  }

  data_extension->WaitForAllReceived();
  double elapsed = timer.Elapsed();
  cout << "Done. Did " << num_trials << " iterations in "
       << elapsed << " seconds. Throughput: "
       << double(num_trials) / elapsed << " per second." << endl;

  ready_monitor->ScheduleSend(new Knot(new string("SHUTDOWN\n")));
  event_loop.ExitLoopAndWait();
  return 0;
}
