//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A script for testing that DB modifications are atomic. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 27 Sep 2012   omd            Original Version
//*****************************************************************

/*bunch of subs via a lot of CallRemoteScripts for each slave harness
LoadedSubscriptionScript with publication file and another file with WaitScript
and CallRemoteScripts for each slave harness
PublishAndModifySubscriptionsScript pub_file delay_func [arg] seed payload_size script_file
-- start pubs in background in new thread
-- execute each script in other file
more pubs via a PublishScript*/

#ifndef CPP_TEST_HARNESS_TA3_SCRIPTS_PUBLISH_AND_MODIFY_SUBSCRIPTIONS_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_SCRIPTS_PUBLISH_AND_MODIFY_SUBSCRIPTIONS_SCRIPT_H_

#include "test-harness/common/test-script.h"

#include <memory>

#include "common/knot.h"
#include "common/line-raw-data.h"
#include "publish-script.h"

class PublishCommand;
class GeneralLogger;
class THRunScriptCommand;
class FirstTokenRawTimeLogFileGenerator;
class MasterHarnessNetworkListener;
class PeriodicRealTimeLogger;

/// This is a versatile script that can instruct the test harness controlling the
/// server to issue any number of database modifications with variable delays
/// while this component runs two theads, one of which generates background
/// traffic with configurable delays and the other thread repeatedly issues
/// queries the correspond to the modifications in an attempt to catch atomicity
/// errors.
class PublishAndModifySubscriptionsScript : public TestScript {
 public:
  typedef boost::function<int ()> DelayFunction;

  /// query_modify_pairs is a file indicating modifications to be performed and
  /// queries to be run at the same time as those modifications in order to catch
  /// atomicity errors. The file is formatted with alternating lines: the first
  /// line indicates the query to perform and the 2nd line is the name of a file,
  /// relative to dir_path, that contains LineRaw formatted data suitable for
  /// VariableDelayModifyArgumentScript (including the delay generator, etc.
  /// 
  /// background_queries is a file containing a set of queries to be sent to the
  /// client in order to provide background traffic. The queries will be sent
  /// using VariableDelayQueryScript using delay_function as the delay.
  PublishAndModifySubscriptionsScript(
      std::istream* modifications, const std::string& dir_path,
      std::istream* background_pubs,
      DelayFunction delay_function,
      PublishCommand* publish_command, int seed,
      TruncatedPoissonNumGenerator payload_size_gen, 
      MasterHarnessNetworkListener* listener, GeneralLogger* logger,
      FirstTokenRawTimeLogFileGenerator* logger_factory, unsigned int timestamp_period);

  virtual ~PublishAndModifySubscriptionsScript();

  virtual void Run();

 private:
  std::istream* modifications_file_;
  PublishCommand* publish_command_;
  MasterHarnessNetworkListener* listener_;
  GeneralLogger* logger_;
  FirstTokenRawTimeLogFileGenerator* logger_factory_;
  std::string config_file_dir_;
  std::auto_ptr<PublishScript> background_runner_;
  GeneralLogger* background_logger_;
  PeriodicRealTimeLogger* background_timestamper_;
  unsigned int timestamp_period_;
};

/// A factory for use with ScriptsFromFile. Expects a line containing, in order,
/// the query_modify_pairs file, the background_queries file, and the delay
/// paramters (as per VariableDelayQueryScript).
class PublishAndModifySubscriptionsScriptFactory {
 public:
  PublishAndModifySubscriptionsScriptFactory(
      PublishCommand* publish_command,
      MasterHarnessNetworkListener* listener,
      FirstTokenRawTimeLogFileGenerator* logger_factory, 
      unsigned int timestamp_period);

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path,
                         GeneralLogger* logger);

 private:
  PublishCommand* publish_command_;
  MasterHarnessNetworkListener* listener_;
  FirstTokenRawTimeLogFileGenerator* logger_factory_;
  unsigned int timestamp_period_;
};

#endif
