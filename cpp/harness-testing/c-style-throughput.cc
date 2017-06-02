#include "common/util.h"
#include "common/timer.h"
#include "common/check.h"
#include "common/check.h"
#include "common/statics.h"
#include <memory>
#include <string>
#include <unistd.h>
#include <vector>

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <cstring>

using namespace std;
namespace po = boost::program_options;

int main(int argc, char** argv) {
  Initialize();

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
  FileHandleOStream process_stdin(process_stdin_h);

  // TODO: call setvbuf...

  Timer timer;
  // Wait until the process is ready
  const int BUFFER_SIZE = 2 << 20;
  char data[BUFFER_SIZE];
  CHECK(read(process_stdout_h, data, BUFFER_SIZE) > 0);
  CHECK(strcmp(data, "READY\n") == 0);
  timer.Start();
  for (int i = 0; i < num_trials; ++i) {
    process_stdin << "GO\n";
    process_stdin.flush();
    bool ready = false;
    while (!ready) {
      size_t bytes_read = read(process_stdout_h, data, BUFFER_SIZE);
      CHECK(bytes_read >= 0);
      if (bytes_read == 0) {
        // We hit EOF - the child must have crashed.
        cerr << "Child process gone." << endl;
        exit(1);
      }

      char* cur_line = data;
      while (cur_line < (data + bytes_read)) {
        if (strncmp(cur_line, "READY\n", sizeof("READY")) == 0) {
          ready = true;
          break;
        }
        size_t bytes_left = bytes_read - (cur_line - data);
        cur_line = (char*) memchr(cur_line, '\n', bytes_left);
        if (cur_line == NULL) {
          break;
        } else {
          cur_line += 1;
        }
      }
    }
  }
  double elapsed = timer.Elapsed();
  cout << "Done. Did " << num_trials << " iterations in "
       << elapsed << " seconds. Throughput: "
       << double(num_trials) / elapsed << " per second." << endl;

  return 0;
}
