//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of PublishAndModifySubscriptionsScript
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 27 Sep 2012   omd            Original Version
//*****************************************************************

#include "publish-and-modify-subscriptions-script.h"

#include "common/future-waiter.h"
#include "common/general-logger.h"
#include "common/line-raw-data.h"
#include "common/safe-file-stream.h"
#include "common/types.h"
#include "common/periodic-real-time-logger.h"
#include "call-remote-script.h"
#include "wait-script.h"
#include "test-harness/common/th-run-script-command.h"
#include "test-harness/common/log-file-generator.h"
#include "test-harness/common/scripts-from-file.h"
#include "test-harness/ta3/commands/publish-command.h"
#include "test-harness/ta3/master-harness-network-listener.h"
#include "test-harness/common/delay-generators.h"
#include "common/periodic-real-time-logger.h"

using std::string;
using std::vector;

PublishAndModifySubscriptionsScript::PublishAndModifySubscriptionsScript(
      std::istream* modifications, const std::string& dir_path,
      std::istream* background_pubs,
      DelayFunction delay_function,
      PublishCommand* publish_command, int seed,
      TruncatedPoissonNumGenerator payload_size_gen, 
      MasterHarnessNetworkListener* listener, GeneralLogger* logger,
      FirstTokenRawTimeLogFileGenerator* logger_factory,
      unsigned int timestamp_period)
    : modifications_file_(modifications), 
      publish_command_(publish_command),
      listener_(listener), logger_(logger), logger_factory_(logger_factory),
      config_file_dir_(dir_path), timestamp_period_(timestamp_period) {
  DCHECK(modifications != NULL);
  DCHECK(background_pubs != NULL);
  background_logger_ = 
    (*logger_factory_)(string("PublishScript for background traffic"));
  background_runner_.reset(
      new PublishScript(background_pubs, delay_function, publish_command_,
                        background_logger_, seed, payload_size_gen));
  background_timestamper_ = new PeriodicRealTimeLogger(background_logger_,
      timestamp_period_);
}

PublishAndModifySubscriptionsScript::~PublishAndModifySubscriptionsScript() {
  delete modifications_file_;
}

void PublishAndModifySubscriptionsScript::Run() {
  ScriptsFromFile scripts_from_file;
  scripts_from_file.AddFactory("CallRemoteScript",
    CallRemoteScriptFileFactory(listener_));
  scripts_from_file.AddFactory("PublishAndModifySubscriptionsScript",
      PublishAndModifySubscriptionsScriptFactory(publish_command_, listener_,
        logger_factory_, timestamp_period_));
  scripts_from_file.AddFactory("WaitScript",
      WaitScriptFactory());
  vector<boost::shared_ptr<TestScript> > scripts_to_run;
  vector<GeneralLogger*> script_loggers;

  DCHECK(background_runner_.get() != NULL);
  LOG(INFO) << "Starting background traffic.";
  background_runner_->RunInThread();
  background_timestamper_->Start();

  LOG(DEBUG) << "Loading modification scripts from " << config_file_dir_;
  scripts_from_file.TestsFromConfiguration(modifications_file_,
                                           config_file_dir_,
                                           *logger_factory_,
                                           &scripts_to_run,
                                           &script_loggers);

  LOG(INFO) << "PublishAndModifySubscriptionsScript will run " 
            << scripts_to_run.size() << " test scripts.";
  vector<boost::shared_ptr<TestScript> >::iterator script_it;
  DCHECK(scripts_to_run.size() == script_loggers.size());
  for (size_t i = 0; i < scripts_to_run.size(); ++i) {
    LOG(INFO) << "Starting test script #" << i;
    PeriodicRealTimeLogger pl(script_loggers[i], timestamp_period_);
    pl.Start();
    scripts_to_run[i]->Run();
    pl.Stop();
    // Free the logger immediately so the file closes and we can score the
    // script.
    delete script_loggers[i];
    LOG(INFO) << "Completed test script #" << i;
  }

  LOG(INFO) << "All modification commands complete";

  LOG(INFO) << "Stopping background traffic";
  background_runner_->Terminate();
  background_timestamper_->Stop();
  delete background_logger_;
  delete background_timestamper_;

  LOG(INFO) << "PublishAndModifySubscriptionsScript complete.";
  logger_->Flush();
}


////////////////////////////////////////////////////////////////////////////////
// PublishAndModifySubscriptionsScriptFactory
////////////////////////////////////////////////////////////////////////////////

PublishAndModifySubscriptionsScriptFactory::PublishAndModifySubscriptionsScriptFactory(
    PublishCommand* publish_command,
    MasterHarnessNetworkListener* listener, 
    FirstTokenRawTimeLogFileGenerator* logger_factory, 
    unsigned int timestamp_period)
    : publish_command_(publish_command), listener_(listener),
      logger_factory_(logger_factory), timestamp_period_(timestamp_period) {
}

TestScript* PublishAndModifySubscriptionsScriptFactory::operator()(
    const string& config_line, const string& dir_path,
    GeneralLogger* logger) {
  LOG(DEBUG) << "Loading PublishAndModifySubscriptions info from "
             << config_line << " and " << dir_path;
  vector<string> parts = Split(config_line, ' ');
  CHECK(parts.size() >= 5);

  CHECK(dir_path.empty() || dir_path.at(dir_path.size() - 1) == '/');
  string pub_path = dir_path + parts[0];
  LOG(DEBUG) << "Loading background pubs from " << pub_path;
  //SafeIFStream pub_file(pub_path.c_str());
  std::ifstream* pub_file = new std::ifstream(pub_path.c_str());

  // TODO(odain): We should have a component that maps delay function names to
  // dealy functions so we don't have to duplicate this.
  if (parts[1] == "NO_DELAY") {
    CHECK(parts.size() == 5);
    TruncatedPoissonNumGenerator ng(SafeAtoi(parts[3]), SafeAtoi(parts[2]));
    string mod_path = dir_path + parts[4];
    LOG(DEBUG) << "Loading mods from " << mod_path;
    std::ifstream* mod_file = new std::ifstream(mod_path.c_str());
    //SafeIFStream mod_file(mod_path.c_str());

    return new PublishAndModifySubscriptionsScript(
        mod_file, dir_path, pub_file, &ZeroDelay,
        publish_command_, SafeAtoi(parts[2]), ng, listener_, logger,
        logger_factory_, timestamp_period_);
  } else {
    CHECK(parts[1] == "EXPONENTIAL_DELAY");
    CHECK(parts.size() == 6);
    // TODO(odain) use strol instead so we can do better error checking.
    int delay_micros = atoi(parts[2].c_str());
    TruncatedPoissonNumGenerator ng(SafeAtoi(parts[4]), SafeAtoi(parts[3]));
    ExponentialDelayFunctor e_delay(delay_micros, SafeAtoi(parts[3]));
    string mod_path = dir_path + parts[5];
    LOG(DEBUG) << "Loading mods from " << mod_path;
    std::ifstream* mod_file = new std::ifstream(mod_path.c_str());
    //SafeIFStream mod_file(mod_path.c_str());

    return new PublishAndModifySubscriptionsScript(
        mod_file, dir_path, pub_file, e_delay,
        publish_command_, SafeAtoi(parts[3]), ng, listener_, logger,
        logger_factory_, timestamp_period_);
  }
}
