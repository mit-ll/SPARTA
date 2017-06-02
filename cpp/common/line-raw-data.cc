//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 27 Sep 2012   omd            Original Version
//*****************************************************************

#include "line-raw-data.h"

#include <cstdlib>
#include <memory>
#include <string>

using std::string;
using std::auto_ptr;

// Called from LineRawDataFromFile. This reads byte count/data pairs out of the
// file until it reaches ENDRAW at which point it returns everything it read.
Knot GetRawData(std::istream* file) {
  Knot result;
  while (file->good()) {
    string byte_count_str;
    getline(*file, byte_count_str);
    CHECK(!byte_count_str.empty());
    if (byte_count_str == "ENDRAW") {
      return result;
    }
    char* end_ptr;
    int byte_count = strtol(byte_count_str.c_str(), &end_ptr, 10);
    CHECK(*end_ptr == '\0') << "Invalid byte count in RAW mode: "
        << byte_count_str;

    CHECK(file->good()) << "Invalid file in the middle of RAW mode.";
    char* data = new char[byte_count];
    file->read(data, byte_count);
    CHECK(!file->fail()) << "Invalid file in the middle of RAW mode.";

    result.Append(data, byte_count);
  }
  LOG(FATAL) << "RAW mode never ended.";
  // This line never actually hit but the compiler needs it.
  return result;
}

void LineRawDataFromFile(std::istream* file,
                         LineRawData<Knot>* output) {
  while (file->good()) {
    auto_ptr<string> line(new string);
    getline(*file, *line);
    if (!file->good()) {
      break;
    }
    if (*line == "RAW") {
      output->AddRaw(GetRawData(file));
    } else {
      output->AddLine(Knot(line.release()));
    }
  }

  CHECK(file->eof()) << "Error reading from file.";

}
