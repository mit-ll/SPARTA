#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <iostream>
#include <string>
#include <vector>

#include "common/check.h"
#include "common/statics.h"

using namespace std;
namespace po = boost::program_options;


void OutputData(unsigned int bytes, unsigned int lines,
                unsigned int chunks_per_line,
                bool flush_lines, bool flush_chunks,
                const vector<char>& byte_source) {
  if (bytes == 0) {
  cout << "DATA\nENDDATA\n";
    return;
  }
  CHECK(byte_source.size() >= bytes);

  unsigned int bytes_per_line = bytes / lines;
  unsigned int bytes_per_chunk = bytes_per_line / chunks_per_line;

  cout << "DATA\n";

  int byte_source_ptr = 0;
  for (unsigned int i = 0; i < lines; ++i) {
    for (unsigned int j = 0; j < chunks_per_line; ++j) {
      cout.write(&byte_source[byte_source_ptr], bytes_per_chunk);
      byte_source_ptr += bytes_per_chunk;
      if (flush_chunks) {
        cout.flush();
      }
    }
    cout << "\n";
    if (flush_lines) {
      cout.flush();
    }
  }

  cout << "ENDDATA\n";
}

int main(int argc, char** argv) {
  Initialize();
  int response_bytes, response_lines, chunks_per_line;
  bool flush_each_line, flush_each_chunk;
  po::options_description desc("Options:");
  desc.add_options()
      ("help,h", "Print help message")
      ("response_bytes,b", po::value<int>(&response_bytes)->default_value(0),
       "In response to 'GO' this will send this many bytes of data before "
       "sending READY")
      ("response_lines,l", po::value<int>(&response_lines)->default_value(1),
       "The --response_bytes bytes of data will be split over this many "
       "lines of output")
      ("chunks_per_line,c", po::value<int>(&chunks_per_line)->default_value(1),
       "Each line of output will be output is this many different pieces")
      ("flush_each_line",
       po::bool_switch(&flush_each_line)->default_value(false),
       "If true cout.flush() is called after each line is written")
      ("flush_each_chunk",
       po::bool_switch(&flush_each_chunk)->default_value(false),
       "If true cout.flush() is called after each chunk is written.");

  po::variables_map vm;
  po::store(po::parse_command_line(argc, argv, desc), vm);
  po::notify(vm);    
  if (vm.count("help")) {
    cout << desc << endl;
    exit(0);
  }
  if (response_bytes != 0) {
    CHECK(response_bytes > 0);
    CHECK(response_lines >= 1);
    CHECK(response_bytes >= response_lines);
    CHECK(response_bytes % response_lines == 0);
    CHECK(chunks_per_line <= (response_bytes/response_lines));
    CHECK((response_bytes/response_lines) % chunks_per_line == 0);
  }

  // Initialize a source of byte data so we don't have to pay the cost to
  // initialize it over and over.
  vector<char> byte_source;
  // We don't anticipate generate more than 1 meg/"GO" so no need to generate
  // more data than that.
  const int MAX_BYTES = 1 << 20;
  CHECK(response_bytes < MAX_BYTES);
  for (int i = 0; i < MAX_BYTES; ++i) {
   byte_source.push_back(i % 256);
  } 

  // Disable stdio synching for performance
  ios_base::sync_with_stdio(false);

  cout << "READY" << endl;
  while (cin.good()) {
    string line;
    getline(cin, line);
    if (line == "GO") {
      OutputData(response_bytes, response_lines, chunks_per_line,
                 flush_each_line, flush_each_chunk,
                 byte_source);
      cout << "READY" << endl;
    } else if (line == "SHUTDOWN") {
      exit(0);
    }
  }

  return 0;
}
