//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of the log factory methods.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 28 Nov 2012   omd            Original Version
//*****************************************************************

#include "log-file-generator.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include "common/general-logger.h"
#include "common/util.h"

using std::string;
using std::vector;

// TODO(njhwang): when we completely convert our code to be C++11 compliant, we
// can take full advantage of delegating constructors and make this a bit
// cleaner
FirstTokenRawTimeLogFileGenerator::FirstTokenRawTimeLogFileGenerator(
    const string& log_dir, bool unbuffered) : 
      log_dir_(log_dir), unbuffered_(unbuffered), 
      header_lines_(vector<string>()) {
  CheckLogDir();
}

FirstTokenRawTimeLogFileGenerator::FirstTokenRawTimeLogFileGenerator(
    const string& log_dir, bool unbuffered, 
    const vector<string>& header_lines) : 
      log_dir_(log_dir), unbuffered_(unbuffered), 
      header_lines_(header_lines) {
  CheckLogDir();
}

GeneralLogger* FirstTokenRawTimeLogFileGenerator::operator()(
    const std::string& config_line) const {
  size_t token_end = config_line.find(' ');
  string first_token = config_line.substr(0, token_end);

  string file_template = log_dir_ + first_token + "-XXXXXX";

  char* log_path = strndup(file_template.data(), file_template.size());

  int fd = mkstemp(log_path);

  if (fd < 0) {
    LOG(FATAL) << "Error opening log file:\n" << strerror(errno);
  }

  FileHandleOStream* log_stream = new FileHandleOStream(fd);
  OstreamRawTimeLogger* logger = 
    new OstreamRawTimeLogger(log_stream, false, unbuffered_);
  if (!header_lines_.empty()) {
    for (auto& header_line : header_lines_) {
      logger->Log(header_line);
    }
  }
  logger->Log(config_line);

  delete log_path;

  return logger;
}

void FirstTokenRawTimeLogFileGenerator::CheckLogDir() {
  CHECK(log_dir_.size() > 0);
  if (*log_dir_.rbegin() != '/') {
    log_dir_ += "/";
  }
}
