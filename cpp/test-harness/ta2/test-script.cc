//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of TestScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Sep 2012  yang            Original Version
//*****************************************************************

#include <stdlib.h>
#include <vector>
#include <fstream>
#include <boost/assign.hpp>
#include "test-script.h"
#include "key-message-handler.h"
#include "circuit-message-handler.h"
#include "input-message-handler.h"
#include "common/util.h"
#include "common/logging.h"
#include "common/timer.h"
#include "common/check.h"

using namespace std;
using namespace boost;

const string TestScript::KEY_DELIM = "KEY";
const string TestScript::CIRCUIT_DELIM = "CIRCUIT";
const string TestScript::INPUT_DELIM = "INPUT";

const std::map<string, string> TestScript::delimToLogDelim = 
  boost::assign::map_list_of
  (TestScript::KEY_DELIM, string("KEYPARAMS")) 
  (TestScript::CIRCUIT_DELIM, TestScript::CIRCUIT_DELIM)
  (TestScript::INPUT_DELIM, TestScript::INPUT_DELIM);

TestScript::TestScript(ostream* log) : 
  client_stdin_(nullptr), client_stdout_(nullptr),
  server_stdin_(nullptr), server_stdout_(nullptr), line_num_(0),
  log_(log) {
}

TestScript::~TestScript() {
  for (auto iter = handlers_.begin(); iter != handlers_.end(); ++iter) {
    delete iter->second;
  }
}

void TestScript::RegisterHandler(const string& delim, MessageHandler* mh) {
  auto key = handlers_.find(delim);
  if (key == handlers_.end()) {
    handlers_.insert(pair<string, MessageHandler*>(delim, mh));
  } else {
    // Replace the previous MessageHandler with the current, making sure to
    // deallocate the original.
    delete handlers_[delim];
    handlers_[delim] = mh;
  }
}

void TestScript::Execute(const string& test_path) {
  ifstream script(test_path.c_str());
  if (script.is_open()) {
    LOG(INFO) << "Running test on path " << test_path;
    Run(script);
    script.close();
    LOG(INFO) << "Completed test.";
  } else {
    LOG(FATAL) << "Cannot open test script file " << test_path;
  }
}

void TestScript::Resume(const string& test_path) {
  LOG(INFO) << "Resuming test on path " << test_path;
  string current_param, current_circuit, line_num;
  // Retrieve the last successful state of the test-harness on its prior
  // execution
  ifstream state("state");
  if (state.is_open()) {
    getline(state, current_param);
    getline(state, current_circuit);
    getline(state, line_num);
    line_num_ = atoi(line_num.c_str());
    if (!current_param.empty()) {
      LOG(INFO) << "Sending most recent security parameter on path "
          << current_param;
      ifstream stream(current_param.c_str());
      handlers_[KEY_DELIM]->Send(&stream);
      SaveState(KEY_DELIM, current_param);
      stream.close();
    }
    if (!current_circuit.empty()) {
      LOG(INFO) << "Sending most recently circuit on path "
          << current_circuit;
      ifstream stream(current_circuit.c_str());
      handlers_[CIRCUIT_DELIM]->Send(&stream);
      SaveState(CIRCUIT_DELIM, current_circuit);
      stream.close();
    }
  } else {
    LOG(FATAL) << "Cannot find recovery info";
  }
  state.close();

  // Seek to the line that caused the crash and run the test from that point
  // forward.
  ifstream script(test_path.c_str());
  if (script.is_open()) {
    string line;
    for (unsigned int i = 0; i < line_num_; ++i) {
      getline(script, line);
    }
    Run(script);
  } else {
    LOG(FATAL) << "Cannot open test script file " << test_path;
  }
  script.close();
  LOG(INFO) << "Completed test.";
}

void TestScript::SaveState(string delim, string path) {
  if (delim == KEY_DELIM) {
    current_param_ = path;
  } else if (delim == CIRCUIT_DELIM) {
    current_circuit_ = path;
  }

  ofstream state("state");
  if (state.is_open()) {
    state << current_param_ << endl;
    state << current_circuit_ << endl;
    state << line_num_ << endl;
  } else {
    LOG(FATAL) << "Cannot save current state";
  }
}

void TestScript::Run(istream& script) {
  string delim, path;
  getline(script, delim);
  ++line_num_;
  while (script.good()) {
    CHECK(handlers_.find(delim) != handlers_.end()) << "Unrecognized delimeter";
    getline(script, path);
    string delim_for_log = delimToLogDelim.find(delim)->second;
    *log_ << delim_for_log << ": " << path << endl;
    *log_ << "TIME: " << GetCurrentTime() << endl;
    ++line_num_;
    ifstream stream(path.c_str());
    if (stream.is_open()) {
      LOG(INFO) << "Processing " << delim << " on path " << path;
      handlers_[delim]->Send(&stream);
      stream.close();
    } else {
      LOG(FATAL) << "Cannot open file on path: " << path;
    }
    SaveState(delim, path);
    getline(script, delim);
    ++line_num_;
  }
  CHECK(script.eof() == true);
}

void TestScript::SpawnClient(const string& client_path, const string& args) {
  LOG(INFO) << "Starting the SUT client with command line arguments: " << args;
  auto_ptr<FileHandleIStream> out;
  auto_ptr<FileHandleOStream> in;
  SpawnAndConnectPipes(client_path, args, &in, &out);
  client_stdout_.reset(new TestHarnessIStream(unique_ptr<istream>(std::move(out))));
  client_stdin_.reset(new TestHarnessOStream(unique_ptr<ostream>(std::move(in))));
}  

void TestScript::SpawnServer(const string& server_path, const string& args) {
  LOG(INFO) << "Starting the SUT server with command line arguments: " << args;
  auto_ptr<FileHandleIStream> out;
  auto_ptr<FileHandleOStream> in;
  SpawnAndConnectPipes(server_path, args, &in, &out);
  server_stdout_.reset(new TestHarnessIStream(unique_ptr<istream>(std::move(out))));
  server_stdin_.reset(new TestHarnessOStream(unique_ptr<ostream>(std::move(in))));
}

void TestScript::SetDebugLogStream(bool buffered) {
  unique_ptr<ostream> server_stdout(new ofstream("server_stdout"));
  server_stdout_->SetDebugLogStream(std::move(server_stdout), buffered);
  unique_ptr<ostream> client_stdout(new ofstream("client_stdout"));
  client_stdout_->SetDebugLogStream(std::move(client_stdout), buffered);
  unique_ptr<ostream> server_stdin(new ofstream("server_stdin"));
  server_stdin_->SetDebugLogStream(std::move(server_stdin), buffered);
  unique_ptr<ostream> client_stdin(new ofstream("client_stdin"));
  client_stdin_->SetDebugLogStream(std::move(client_stdin), buffered);
}

void TestScript::InitHandlers() {
  for (auto iter = handlers_.begin(); iter != handlers_.end(); ++iter) {
    iter->second->set_client_stdin(client_stdin_.get());
    iter->second->set_client_stdout(client_stdout_.get());
    iter->second->set_server_stdin(server_stdin_.get());
    iter->second->set_server_stdout(server_stdout_.get());
  }
}

