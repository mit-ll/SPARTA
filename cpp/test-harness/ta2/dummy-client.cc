//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        A dummy client for harness testing 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012  yang            Original Version
//*****************************************************************

#include <cstdlib>
#include <string>
#include <iostream>
#include "common/logging.h"
#include "common/statics.h"
#include "common/check.h"
#include "common/string-algo.h"

using namespace std;

// This is a really dumb baseline client. It simply outputs a public key of 0,
// echos the unencrypted input as encrypted output, and echos the encrypted
// result as unencrypted result.
int main(int argc, const char* argv[]) {
  Initialize();
  string line;
  while( getline(cin, line) ) {
    if (line == "KEY") {
      // consume the security param
      getline(cin, line);
      while (line != "ENDKEY") {
        getline(cin, line);
      }
      CHECK(line == "ENDKEY") << "Unexpected key message footer" << line;
      // return the public key
      cout << "KEY\n0\nENDKEY" << endl;
    } else if (line == "PDATA") {
      string input;
      // consume the plain-text input
      getline(cin, input);
      CHECK(line.size() > 0) << "Did not receive an input";
      // consume the message footer
      getline(cin, line);
      CHECK(line == "ENDPDATA") << "Unexpected PDATA footer" << line;
      cout << "EDATA\n" << input.size() << "\n";
      cout.write(input.c_str(), input.size());
      cout << "ENDEDATA" << endl;
    } else if (line == "EDATA") {
      string temp;
      getline(cin, temp);
      CHECK(temp.size() > 0) << "Did not receive an encrypted output";
      int size = SafeAtoi(temp);
      char output[size];
      cin.read(output, size);
      getline(cin, temp);
      CHECK(temp == "ENDEDATA") << "Unexpected EDATA footer" << temp;
      cout << "PDATA\n";
      cout.write(output, size);
      cout << "\nENDPDATA" << endl;
    } 
  }
  return 0;
}
