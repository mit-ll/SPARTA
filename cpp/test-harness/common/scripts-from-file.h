//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A framework for constructing TestScript objects from a
//                     configuration file. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_SCRIPTS_FROM_FILE_H_
#define CPP_TEST_HARNESS_COMMON_SCRIPTS_FROM_FILE_H_

#include <boost/shared_ptr.hpp>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "common/general-logger.h"

class TestScript;

/// Each performer has a different set of test scripts we have to run. The
/// differences are both the general TestScript class being used and the
/// parameters passed to the constructor of that script. For example, two TA1
/// performers will both have an unloaded query latency test, but that test will
/// be initialized with different files so they can be provided with different
/// queries. In addition, some performers will run tests that others skip (e.g.
/// the throughput tests aren't necessary if the performer doesn't support
/// concurrent execution). In order to simplify the configuration of all of this
/// we have a very general framework here. This framework reads lines from a
/// configuration file. The 1st token in the line identifies a factory function
/// that knows how to make an appropriate TestScript object. That factory parses
/// the rest of the line and converts things to tokens as appropriate.
class ScriptsFromFile {
 public:
  ScriptsFromFile() {}
  virtual ~ScriptsFromFile() {}

  /// The type of a factory function (or functor). It gets called with
  /// everything on the configuration file line *except* the token that
  /// identified the factory to use. The 2nd argument is the directory where
  /// the configuration file was located. Some constructors use this so they
  /// can open addititional configuration files (e.g. a list of queries to run)
  /// relative to that directory. The directory is assumed to be supplied
  /// *with* a trailing '/' character unless all paths are relative to the
  /// current directory in which case it's the empty string.
  typedef std::function<TestScript* (const std::string&, const std::string&,
                                     GeneralLogger*)>
      ScriptFactory;
  void AddFactory(const std::string& id_token, ScriptFactory factory);

  typedef std::function<GeneralLogger* (const std::string&)> LoggerFactory;
  /// Parses the configuration lines in input_file and fill in the tests vector
  /// with the test to be run. Input file is assumed to be in input_file_dir.
  /// Unit tests may pass an empty input_file_dir and only instantiate TestScript
  /// objects that don't require a valid path. On return loggers[i] will hold the
  /// GeneralLogger instance used by tests[i]. We do this instead of having the
  /// tests take a shared_ptr or something so we can easily have the main method
  /// decide when log files should be closed. For example, we dont' want to delay
  /// closing files as that means we can't start scoring a test until all scripts
  /// are complete.
  void TestsFromConfiguration(
      std::istream* input_file,
      const std::string& input_file_dir,
      LoggerFactory logger_factory,
      std::vector<boost::shared_ptr<TestScript> >* tests,
      std::vector<GeneralLogger*>* loggers);

 private:
  std::map<std::string, ScriptFactory> factory_map_;
};

#endif
