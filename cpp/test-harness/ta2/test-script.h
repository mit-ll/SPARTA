//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        A TestScript that executes a specified test 
//
// Modifications:
// Date          Name           Modification
// ----         ----           ------------
// 25 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA2_TEST_SCRIPT_H_
#define CPP_TEST_HARNESS_TA2_TEST_SCRIPT_H_

#include <string>
#include <map>
#include "key-message-handler.h"
#include "circuit-message-handler.h"
#include "input-message-handler.h"
#include "stream-util.h"

// A TestScript spawns the client and server instances of the SUT or baseline
// and executes a series of key exchange, circuit ingestion, and homomorphic
// evaluation rounds. A TestScript object coordinates the communication between
// the client and server using a set of message handlers. The actual
// communication is performed by the message handlers.
class TestScript {
 public:

  TestScript(std::ostream* log);

  // Frees all registered MessageHandlers.
  ~TestScript();

  // Begin a test. This method takes as input a file path to the test script.
  // Each test script contains delimiters followed immediately by relative paths
  // to other files containing the security parameter, circuit description, and 
  // inputs. Any number of circuits can be specified per security parameter. In 
  // addition, any number of inputs can be specified per circuit description. An 
  // example test script might look like:
  //
  // KEY
  // path/to/key1
  // CIRCUIT
  // path/to/circuit1
  // INPUT
  // path/to/input1
  // INPUT
  // path/to/input2
  // CIRCUIT
  // path/to/circuit2
  //
  // This method parses the test script line-by-line and passes the file path to
  // the correct message handler indicated by the delimter. If an unexpected
  // delimeter is encountered, the function will abort the test.
  void Execute(const std::string& test_path);

  // In the test-harness crashes at any point during its execution, calling
  // Resume() will begin the test-harness in the most recent state prior to the
  // crash. This means that all successfully run key-exchanges, injestions, and
  // evaluations will *not* be run again. Calling Resume() if a test
  // successfully completes does nothing.
  void Resume(const std::string& test_path);

  // The test-harness will create four file streams that log the stdin/stdout of
  // the client/server. Setting a logger may impact the performance of executing
  // tests. These files can also become quite large.
  void SetDebugLogStream(bool buffered);

  // Registers a MessageHandler with the TestScript. Each MessageHandler is tied
  // to a specific delimiter. When the TestScript parses a delimeter, it
  // executes the corresponding MessageHandler by passing it a file stream. 
  // The TestScript takes ownership of the MessageHandlers.
  void RegisterHandler(const std::string& delim, MessageHandler* mh);
  
  // Spawns the client process, passing it the arguments specified in args.
  void SpawnClient(const std::string& client_path, const std::string& args);

  // Spawns the server process, passing it the arguments specified in args.
  void SpawnServer(const std::string& server_path, const std::string& args);

  // After the client and server processes have been spawned, InitHandlers will
  // assign the client and server stdin/outs to each registered MessageHandler.
  // This method must be called once before the first call to Execute().
  void InitHandlers();

  // These static constants define the string sequence used to identity each
  // delimeter used in the test file.
  const static std::string KEY_DELIM;
  const static std::string CIRCUIT_DELIM;
  const static std::string INPUT_DELIM;

 private:

  void SaveState(std::string delim, std::string path);
  void Run(std::istream& script);

  std::unique_ptr<TestHarnessOStream> client_stdin_;
  std::unique_ptr<TestHarnessIStream> client_stdout_;
  std::unique_ptr<TestHarnessOStream> server_stdin_;
  std::unique_ptr<TestHarnessIStream> server_stdout_;
 
  std::map<std::string, MessageHandler*> handlers_;
  std::string current_param_;
  std::string current_circuit_;
  unsigned int line_num_;
  std::ostream* log_;

  // Get the keyword to output to the log file from the keyword to 
  // use with the client and servers
  const static std::map<std::string, std::string> delimToLogDelim;

};

#endif
