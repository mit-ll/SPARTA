//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for ScriptsFromFile 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE ScriptsFromFileTest
#include "common/test-init.h"

#include "scripts-from-file.h"

#include <memory>
#include <sstream>
#include <vector>

#include "common/general-logger.h"
#include "test-script.h"

using namespace std;

// Appends "Script1: X", where X is the rest of the configuration line in the
// configuration file that caused the script to be constructed, to the end of
// output. output can then be inspected in the test to ensure the test ran.
class Script1 : public TestScript {
 public:
  Script1(const string& config_line, vector<string>* output)
      : config_line_(config_line),
        output_(output) {}

  virtual ~Script1() {}

  virtual void Run() {
    output_->push_back("Script1: " + config_line_);
  }

 private:
  string config_line_;
  vector<string>* output_;
};

// The same as Script1 but writes "Script2: X".
class Script2 : public TestScript {
 public:
  Script2(const string& config_line, vector<string>* output)
      : config_line_(config_line), output_(output) {}

  virtual ~Script2() {}

  virtual void Run() {
    output_->push_back("Script2: " + config_line_);
  }

 private:
  string config_line_;
  vector<string>* output_;
};

// tempated functor that can construct a Script1 or a Script2
template<class ScriptT>
class ConstructFunctor {
 public:
  ConstructFunctor(vector<string>* output)
      : output_(output) {}

  TestScript* operator()(const string& rest_of_line,
                         const string& dir_path,
                         GeneralLogger* logger) {
    BOOST_CHECK(logger == nullptr);
    return new ScriptT(rest_of_line, output_);
  }

 private:
  vector<string>* output_;
};

BOOST_AUTO_TEST_CASE(ScriptsFromFileWorks) {
  ScriptsFromFile sff;
  vector<string> results;
  sff.AddFactory("Script1", ConstructFunctor<Script1>(&results));
  sff.AddFactory("Script2", ConstructFunctor<Script2>(&results));

  ScriptsFromFile::LoggerFactory log_factory =
      [](const string& line){ return static_cast<GeneralLogger*>(nullptr); };

  istringstream config_file(
      "Script1 First Script\n"
      "Script2 Second Script\n"
      "Script1 Third Script\n");
  vector<boost::shared_ptr<TestScript> > scripts;
  vector<GeneralLogger*> script_loggers;
  sff.TestsFromConfiguration(&config_file, "", log_factory, &scripts,
                             &script_loggers);

  vector<boost::shared_ptr<TestScript> >::iterator i;
  for (i = scripts.begin(); i != scripts.end(); ++i) {
    (*i)->Run();
  }

  BOOST_REQUIRE_EQUAL(results.size(), 3);
  BOOST_CHECK_EQUAL(results[0], "Script1: First Script");
  BOOST_CHECK_EQUAL(results[1], "Script2: Second Script");
  BOOST_CHECK_EQUAL(results[2], "Script1: Third Script");
}
