//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ScriptsFromFile
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012   omd            Original Version
//*****************************************************************

#include "scripts-from-file.h"

#include "test-script.h"

using namespace std;

void ScriptsFromFile::AddFactory(const string& id_token,
                                 ScriptFactory factory) {
  DCHECK(factory_map_.find(id_token) == factory_map_.end());
  factory_map_.insert(make_pair(id_token, factory));
}

void ScriptsFromFile::TestsFromConfiguration(
    istream* input_file, const string& input_file_dir,
    LoggerFactory logger_factory,
    vector<boost::shared_ptr<TestScript> >* tests,
    vector<GeneralLogger*>* loggers) {
  while (input_file->good()) {
    string line;
    getline(*input_file, line);
    if (!line.empty()) {
      DCHECK(tests->size() == loggers->size());
      GeneralLogger* logger(logger_factory(line));
      size_t token_end = line.find(' ');
      string token = line.substr(0, token_end);
      map<string, ScriptFactory>::iterator s_it =
          factory_map_.find(token);
      CHECK(s_it != factory_map_.end())
          << "Could not find script matching: '" << token << "'";

      string rest_of_line;
      if (token_end == string::npos) {
        rest_of_line = "";
      } else {
        rest_of_line = line.substr(token_end + 1, string::npos);
      }
      LOG(DEBUG) << "Constructing test script: " << token;
      boost::shared_ptr<TestScript>
          script(s_it->second(rest_of_line, input_file_dir, logger));
      tests->push_back(script);
      loggers->push_back(logger);
      DCHECK(tests->size() == loggers->size());
    }
  }

  CHECK(input_file->eof()) << "Error reading configuration file";
}
