//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        A script for sending publication requests to the server
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_PUBLISH_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_PUBLISH_SCRIPT_H_

#include "test-harness/common/test-script.h"

#include <thread>
#include <functional>

#include "test-harness/ta3/pub-sub-gen/num-predicate-generators.h"
#include "common/line-raw-data.h"
#include "common/knot.h"
#include "common/conditions.h"

class PublishCommand;
class GeneralLogger;
class DelayFunction;
class TruncatedPoissonNumGenerator;

class PublishScript : public TestScript {
 public:
  typedef std::function<int ()> DelayFunction;

  /// publish_sequence: sequence of publications consisting of METADATA, comma
  /// separated list of metadata, PAYLOAD, some payload in any line raw format,
  /// and ENDPAYLOAD
  /// TODO let this class support different payload_size_gen classes
  PublishScript(
      std::istream* publish_file,
      DelayFunction delay_function, PublishCommand* publish_command, 
      GeneralLogger* logger, int seed, 
      TruncatedPoissonNumGenerator payload_size_gen);

  virtual ~PublishScript();

  virtual void Run();

  virtual void Terminate();

 private:
  LineRawData<Knot>* ParsePublishSequence();

  void LogPublishCommandStatus(
      size_t command_id, const char* state);

  std::istream* publish_file_;
  DelayFunction delay_function_;
  PublishCommand* publish_command_;
  GeneralLogger* logger_;
  TruncatedPoissonNumGenerator payload_size_gen_;
  std::uniform_int_distribution<int> byte_gen_;
  std::mt19937 rng_;
  /// Set to true by Terminate()
  bool should_stop_;
  std::mutex should_stop_tex_;
  SimpleCondition<bool> script_complete_;

  /*std::vector<LineRawData<Knot>*> commands_;

  enum State { WAITING_METADATA, PROCESSING_METADATA, WAITING_PAYLOAD,
               PROCESSING_PAYLOAD };
  State state;*/
};

/// A factory for use with ScriptsFromFile. Expects a line containing, in order,
/// the query_modify_pairs file, the background_queries file, and the delay
/// parameters (as per VariableDelayQueryScript).
class PublishScriptFactory {
 public:
  PublishScriptFactory(
      PublishCommand* publish_command);

  TestScript* operator()(const std::string& config_line,
                         const std::string& dir_path, 
                         GeneralLogger* logger);

 private:
  PublishCommand* publish_command_;
};

#endif
