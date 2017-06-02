#include "common/util.h"
#include "common/timer.h"
#include "common/check.h"
#include "common/check.h"
#include "common/statics.h"
#include <memory>
#include <string>
#include <vector>

#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>

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

  // Disable stdio synching for performance
  ios_base::sync_with_stdio(false);

  auto_ptr<FileHandleIStream> process_stdout;
  auto_ptr<FileHandleOStream> process_stdin;

  SpawnAndConnectPipes(
      executable, args, &process_stdin, &process_stdout);

  // Make a big buffer for stdin.
  const int BUFFER_SIZE = 2 << 20;
  char buffer[BUFFER_SIZE];
  process_stdout->rdbuf()->pubsetbuf(buffer, BUFFER_SIZE);

  Timer timer;
  // Wait until the process is ready
  string line;
  line.reserve(2 << 20);
  getline(*process_stdout, line);
  CHECK(line == "READY");
  timer.Start();
  for (int i = 0; i < num_trials; ++i) {
    *process_stdin << "GO\n";
    process_stdin->flush();
    line = "";
    while (line != "READY") {
      getline(*process_stdout, line);
    }
  }
  double elapsed = timer.Elapsed();
  cout << "Done. Did " << num_trials << " iterations in "
       << elapsed << " seconds. Throughput: "
       << double(num_trials) / elapsed << " per second." << endl;

  return 0;
}
