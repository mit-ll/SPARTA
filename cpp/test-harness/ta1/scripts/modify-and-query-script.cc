//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ModifyAndQueryScript
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 27 Sep 2012   omd            Original Version
//*****************************************************************

#include "modify-and-query-script.h"

#include "common/future-waiter.h"
#include "common/general-logger.h"
#include "common/line-raw-data.h"
#include "common/safe-file-stream.h"
#include "common/types.h"
#include "test-harness/common/th-run-script-command.h"
#include "test-harness/ta1/query-command.h"
#include "test-harness/common/delay-generators.h"

using std::string;
using std::vector;

ModifyAndQueryScript::ModifyAndQueryScript(
    std::istream* query_modify_pairs, const std::string& dir_path,
    std::istream* background_queries, DelayFunction delay_function,
    THRunScriptCommand* run_script_command, QueryCommand* query_command,
    GeneralLogger* logger)
    : run_script_command_(run_script_command), query_command_(query_command),
      logger_(logger) {
  DCHECK(query_modify_pairs != NULL);
  if (background_queries != NULL) {
    background_runner_.reset(
        new VariableDelayQueryScript(background_queries, -1, query_command_,
                                     logger_, delay_function));
  }

  ParseQueryModifyPairs(query_modify_pairs, dir_path);
}

ModifyAndQueryScript::~ModifyAndQueryScript() {
  std::vector<LineRawData<Knot>*>::iterator i;
  for (i = modifications_.begin(); i != modifications_.end(); ++i) {
    delete *i;
  }
}

void ModifyAndQueryScript::ParseQueryModifyPairs(std::istream* input_file,
                                                 const std::string& dir_path) {
  CHECK(queries_.size() == modifications_.size());
  CHECK(dir_path.empty() || dir_path.at(dir_path.size() - 1) == '/');
  while (input_file->good()) {
    string* line = new string;
    getline(*input_file, *line);
    if (line->empty()) {
      delete line;
      continue;
    }
    Knot query_knot(line);
    // The first line should be a query.
    Knot query_id_knot = query_knot.Split(query_knot.Find('S'));
    CHECK(query_knot.StartsWith("SELECT")) << "Invalid query specification: " 
                                           << *line;
    query_knot.AppendOwned("\n", 1);
    queries_.push_back(query_knot);
    query_ids_.push_back(ConvertString<uint64_t>(query_id_knot.ToString()));
    // The next line should be a relative path to a file containing the command
    // data for the server harness.
    CHECK(input_file->good());
    string rel_file_path;
    getline(*input_file, rel_file_path);
    CHECK(!input_file->fail());
    string full_file_path = dir_path + rel_file_path;
    SafeIFStream remote_command_file(full_file_path.c_str());
    LineRawData<Knot>* remote_command_data = new LineRawData<Knot>;
    LineRawDataFromFile(&remote_command_file, remote_command_data);
    CHECK(remote_command_data->Size() > 0);
    modifications_.push_back(remote_command_data);
  }

  CHECK(input_file->eof()) << "Reading query/modifier pairs file failed.";
  CHECK(queries_.size() == modifications_.size());
}

void ModifyAndQueryScript::Run() {
  if (background_runner_.get() != NULL) {
    LOG(INFO) << "Starting background traffic.";
    background_runner_->RunInThread();
  }

  LOG(INFO) << "ModifyAndQueryScript running "
      << queries_.size() << " modification/query pairs";
  DCHECK(queries_.size() == modifications_.size());
  for (size_t i = 0; i < queries_.size(); ++i) {
    LOG(INFO) << "Sending DB modification command " << i
        << " to the server harness.";
    // Will wait for all our query commands to complete
    FutureWaiter<Knot> waiter;
    // Start sending one query before we send the RUNSCRIPT command to increase
    // our chances of finding atomicity issues.
    waiter.Add(
        query_command_->Schedule(i, query_ids_[i], queries_[i], logger_));

    // Start the modify command
    THRunScriptCommand::ResultsFuture f_started, f_done;
    run_script_command_->SendRunScript(*modifications_[i], f_started, f_done);
    f_started.AddCallback(
        std::bind(&ModifyAndQueryScript::LogModificationCommandStatus,
                    this, i, "STARTED"));

    // And keep sending the query until the modify command is done. Make sure no
    // more than 10 of the queries are outstanding at a time so that we don't
    // have a huge queue of queries to process after the modification finishes.
    const int kMaxPendingQueries = 10;
    int num_pending = 0;
    std::mutex num_pending_tex;
    std::condition_variable num_pending_count_low;
    while (!f_done.HasFired()) {
      {
        MutexGuard g(num_pending_tex);
        ++num_pending;
      }
      auto f = query_command_->Schedule(i, query_ids_[i], queries_[i], logger_);
      waiter.Add(f);
      f.AddCallback([&num_pending, &num_pending_tex, &num_pending_count_low]
                    (const Knot& v) {
                      MutexGuard g(num_pending_tex);
                      --num_pending;
                      if (num_pending < kMaxPendingQueries) {
                        num_pending_count_low.notify_all();
                      }
                    });

      {
        std::unique_lock<std::mutex> lock(num_pending_tex);
        while (num_pending >= kMaxPendingQueries) {
          num_pending_count_low.wait(lock);
        }
      }
    }
    LOG(INFO) << "Modification command " << i << " complete";
    LOG(INFO) << "Waiting for queued queries to complete.";
    LogModificationCommandStatus(i, "FINISHED");
    waiter.Wait();
    LOG(INFO) << "All pending queries complete.";
  }

  LOG(INFO) << "All modification commands complete";

  if (background_runner_.get() != NULL) {
    LOG(INFO) << "Stopping background traffic";
    background_runner_->Terminate();
  }
  LOG(INFO) << "ModifyAndQueryScript complete.";
  logger_->Flush();
}

void ModifyAndQueryScript::LogModificationCommandStatus(
    size_t global_id, const char* state) {
  std::ostringstream out;
  out << "Modification command " << global_id << " " << state;
  logger_->Log(out.str());
}

////////////////////////////////////////////////////////////////////////////////
// ModifyAndQueryScriptConstructor
////////////////////////////////////////////////////////////////////////////////

ModifyAndQueryScriptConstructor::ModifyAndQueryScriptConstructor(
    THRunScriptCommand* run_script_command, QueryCommand* query_command)
    : run_script_command_(run_script_command), query_command_(query_command) {
}

TestScript* ModifyAndQueryScriptConstructor::operator()(
    const string& config_line, const string& dir_path,
    GeneralLogger* logger) {
  vector<string> parts = Split(config_line, ' ');
  CHECK(parts.size() >= 3);

  CHECK(dir_path.empty() || dir_path.at(dir_path.size() - 1) == '/');
  string query_mod_path = dir_path + parts[0];
  SafeIFStream query_mod_file(query_mod_path.c_str());

  string bg_query_path = dir_path + parts[1];
  SafeIFStream bg_query_file(bg_query_path.c_str());

  // TODO(odain): We should have a component that maps delay function names to
  // dealy functions so we don't have to duplicate this.
  if (parts[2] == "NO_DELAY") {
    CHECK(parts.size() == 3);
    return new ModifyAndQueryScript(
        &query_mod_file, dir_path, &bg_query_file, &ZeroDelay,
        run_script_command_, query_command_, logger);
  } else {
    CHECK(parts[2] == "EXPONENTIAL_DELAY");
    CHECK(parts.size() == 4);
    // TODO(odain) use strol instead so we can do better error checking.
    int delay_micros = atoi(parts[3].c_str());
    const int kRandomSeed = 0;
    ExponentialDelayFunctor e_delay(delay_micros, kRandomSeed);

    return new ModifyAndQueryScript(
        &query_mod_file, dir_path, &bg_query_file, e_delay,
        run_script_command_, query_command_, logger);
  }
}
