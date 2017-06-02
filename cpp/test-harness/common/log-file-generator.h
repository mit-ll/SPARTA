//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Constructs GeneralLogger instances from script
//                     configurations. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 28 Nov 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_LOG_FILE_GENERATOR_H_
#define CPP_TEST_HARNESS_COMMON_LOG_FILE_GENERATOR_H_

#include <string>
#include <vector>

class GeneralLogger;

/// See ScriptsFromFile to get the basic idea for how this is used. This
/// generator constructs a GeneralLogger from the 1st token on the script
/// configuration line. It then writes the entire script config line to the file.
class FirstTokenRawTimeLogFileGenerator {
 public:
  FirstTokenRawTimeLogFileGenerator(const std::string& log_dir, bool unbuffered);
  FirstTokenRawTimeLogFileGenerator(const std::string& log_dir, bool unbuffered,
      const std::vector<std::string>& header_lines);

  GeneralLogger* operator()(const std::string& config_line) const;

 private:
  void CheckLogDir();

  std::string log_dir_;
  bool unbuffered_;
  std::vector<std::string> header_lines_;
};

#endif
