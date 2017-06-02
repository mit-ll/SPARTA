//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of PublishScript
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "publish-script.h"

#include <fstream>
#include <memory>
#include <thread>

#include "test-harness/ta3/pub-sub-gen/num-predicate-generators.h"
#include "test-harness/ta3/commands/publish-command.h"
#include "test-harness/common/delay-generators.h"
#include "common/general-logger.h"
#include "common/line-raw-data.h"

using namespace std;

PublishScript::PublishScript(
    std::istream* publish_file,
    DelayFunction delay_function, PublishCommand* publish_command, 
    GeneralLogger* logger, int seed, 
    TruncatedPoissonNumGenerator payload_size_gen)
    : publish_file_(publish_file), delay_function_(delay_function),
      publish_command_(publish_command), logger_(logger), 
      payload_size_gen_(payload_size_gen), byte_gen_(33, 126), rng_(seed),
      should_stop_(false), script_complete_(false) {
  LOG(DEBUG) << "PublishScript initialized with seed " << seed;
  DCHECK(publish_file != NULL);
}

PublishScript::~PublishScript() {
  delete publish_file_;
}

LineRawData<Knot>* PublishScript::ParsePublishSequence() {
  enum State { WAITING_METADATA, PROCESSING_METADATA, WAITING_PAYLOAD,
               PROCESSING_PAYLOAD };
  State state = WAITING_METADATA;
  LineRawData<Knot>* command_data = new LineRawData<Knot>;

  while (1) {
    LineRawData<Knot>* publish_data = new LineRawData<Knot>;
    if (publish_file_->good()) {
      auto_ptr<string> line(new string);
      getline(*publish_file_, *line);
      if (line->length() == 0) {
        continue;
      }
      if (*line == "RAW") {
        publish_data->AddRaw(GetRawData(publish_file_));
      } else {
        publish_data->AddLine(Knot(line.release()));
      }
    } else {
      DCHECK(state == WAITING_METADATA);
      delete publish_data;
      delete command_data;
      break;
    }
    switch (state) {
      case WAITING_METADATA:
        CHECK(!publish_data->IsRaw(0));
        CHECK(publish_data->Get(0).ToString() == "METADATA") << 
          "Expected METADATA; received " << 
           publish_data->Get(0).ToString();
        state = PROCESSING_METADATA;
        break;
      case PROCESSING_METADATA: {
        CHECK(!publish_data->IsRaw(0));
        command_data->AddLine(publish_data->Get(0));
        size_t payload_size = payload_size_gen_();
        char payload_arr[payload_size];
        for (size_t i = 0; i < payload_size; i++) {
          payload_arr[i] = byte_gen_(rng_);
        }
        string* payload_str(new string(payload_arr, payload_size));
        command_data->AddRaw(Knot(payload_str));
        delete publish_data;
        return command_data;
      } default:
        LOG(FATAL) << "This should never happen!";
    }
    delete publish_data;
  }
  return nullptr;
}

void PublishScript::Run() {
  LOG(INFO) << "Sending publication commands...";
  size_t command_count = 0;
  while (1) {
    {
      MutexGuard l(should_stop_tex_);
      if (should_stop_) {
        LOG(INFO) << "PublishScript interrupted. Exiting";
        script_complete_.Set(true);
        break;
      }
    }
    LineRawData<Knot>* command_data = ParsePublishSequence();
    if (command_data == nullptr) {
      delete command_data;
      script_complete_.Set(true);
      break;
    }
    LogPublishCommandStatus(++command_count, "STARTED");
    LOG(DEBUG) << "Sending the command: " << command_data->LineRawOutput();
    NumberedCommandSender::ResultsFuture f = 
      publish_command_->Schedule(*command_data, logger_);
    LOG(DEBUG) << "Waiting for command results...";
    f.Wait();
    LOG(DEBUG) << "Received command results";
    LogPublishCommandStatus(command_count, "FINISHED");
    int delay_us = delay_function_();
    if (delay_us > 0) {
      std::this_thread::sleep_for(std::chrono::microseconds(delay_us));
    }
    delete command_data;
  }
  logger_->Flush();
  LOG(INFO) << "All publication commands completed";
}

void PublishScript::LogPublishCommandStatus(
    size_t command_id, const char* state) {
  std::ostringstream out;
  out << "PublishScript publish command #" << command_id << " " << state;
  logger_->Log(out.str());
}

void PublishScript::Terminate() {
  {
    MutexGuard l(should_stop_tex_);
    LOG(DEBUG) << "PublishScript received terminate signal";
    should_stop_ = true;
  }
  script_complete_.Wait(true);
}

////////////////////////////////////////////////////////////////////////////////
// PublishScriptFactory
////////////////////////////////////////////////////////////////////////////////

PublishScriptFactory::PublishScriptFactory(
    PublishCommand* publish_command)
    : publish_command_(publish_command) {
}

TestScript* PublishScriptFactory::operator()(
    const string& config_line, const string& dir_path, GeneralLogger* logger) {
  vector<string> parts = Split(config_line, ' ');
  CHECK(parts.size() >= 2);

  CHECK(dir_path.empty() || dir_path.at(dir_path.size() - 1) == '/');
  string publish_file_path = dir_path + parts[0];
  std::ifstream* publish_file = new std::ifstream(publish_file_path.c_str());

  // TODO(njhwang) We should have a component that maps delay function names to
  // delay functions so we don't have to duplicate this.
  if (parts[1] == "NO_DELAY") {
    CHECK(parts.size() >= 4);
    CHECK(parts.size() < 6);
    // TODO let this handle constant size
    TruncatedPoissonNumGenerator ng(SafeAtoi(parts[3]), SafeAtoi(parts[2]));
    return new PublishScript(
        publish_file, &ZeroDelay,
        publish_command_, logger, SafeAtoi(parts[2]), ng);
  } else {
    CHECK(parts[1] == "EXPONENTIAL_DELAY");
    CHECK(parts.size() >= 5);
    CHECK(parts.size() < 7);
    // TODO(njhwang) use strol instead so we can do better error checking.
    int delay_micros = atoi(parts[2].c_str());
    TruncatedPoissonNumGenerator ng(SafeAtoi(parts[4]), SafeAtoi(parts[3]));
    ExponentialDelayFunctor e_delay(delay_micros, SafeAtoi(parts[3]));

    return new PublishScript(
        publish_file, e_delay,
        publish_command_, logger, SafeAtoi(parts[3]), ng);
  }
}
