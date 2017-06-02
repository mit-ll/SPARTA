#include <boost/program_options/options_description.hpp>
#include <boost/program_options/parsers.hpp>
#include <boost/program_options/variables_map.hpp>
#include <boost/thread.hpp>
#include <iostream>
#include <string>
#include <vector>
#include <random>
#include <chrono>

#include "common/check.h"
#include "common/statics.h"
#include "common/string-algo.h"

using namespace std;

int main(int argc, char** argv) {
  Initialize();

  unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
  default_random_engine generator(seed);
  uniform_int_distribution<int> coin_toss(0,1);
  uniform_int_distribution<int> ms_delay(0,200);

  // Disable stdio synching for performance
  ios_base::sync_with_stdio(false);

  cout << "READY" << endl;
  while (cin.good()) {
    string line;
    getline(cin, line);
    if (line.find("COMMAND") == 0) {
      int cmd_num = SafeAtoi(line.substr(line.find_first_of(' ') + 1,
                                         string::npos));
      while (line != "ENDCOMMAND") {
        getline(cin, line);
      }
      //boost::this_thread::sleep(boost::posix_time::milliseconds(ms_delay(generator)));
      if (coin_toss(generator)) {
        cout << "RESULTS " << cmd_num << "\nDONE\nENDRESULTS" << endl;
      } else {
        cout << "RESULTS " << cmd_num <<
          "\nFAILED\nboohoo\nENDFAILED\nENDRESULTS" << endl;
      }
    } else if (line == "CLEARCACHE") {
      //boost::this_thread::sleep(boost::posix_time::milliseconds(ms_delay(generator)));
      cout << "DONE" << endl;
    } else if (line == "SHUTDOWN") {
      exit(0);
    }
    if (coin_toss(generator)) {
      cout <<
        "PUBLICATION\nPAYLOAD\nRAW\n5\nhelloENDRAW\nENDPAYLOAD\nENDPUBLICATION\nREADY" <<
        endl;
    } else {
      cout << "READY" << endl;
    }
  }

  return 0;
}
