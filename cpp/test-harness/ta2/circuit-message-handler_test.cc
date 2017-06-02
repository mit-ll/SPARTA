#include <sstream>
#include "circuit-message-handler.h"

#define BOOST_TEST_MODULE 
#define BOOST_TEST_DYN_LINK

#include <boost/test/unit_test.hpp>
#include "common/test-init.h"

using namespace std;

BOOST_AUTO_TEST_CASE(CircuitHandlerWorks) {
  stringstream* server_stdin_handle = new stringstream();
  unique_ptr<stringstream> server_stdin_ptr(server_stdin_handle);
  TestHarnessOStream server_stdin(move(server_stdin_ptr));

  stringstream* server_stdout_handle = new stringstream();
  unique_ptr<stringstream> server_stdout_ptr(server_stdout_handle);
  TestHarnessIStream server_stdout(move(server_stdout_ptr));

  auto_ptr<stringstream> results(new stringstream());

  auto c = CircuitMessageHandler(results.get());
  c.set_server_stdin(&server_stdin);
  c.set_server_stdout(&server_stdout);

  *server_stdout_handle << "CIRCUIT\nCIRCUIT READY\nENDCIRCUIT" << endl;

  stringstream file;
  file << "This\nIs\nA\nCircuit";
  c.Send(&file);

  BOOST_CHECK_EQUAL(
      server_stdin_handle->str(), "CIRCUIT\nThis\nIs\nA\nCircuit\nENDCIRCUIT\n");
  BOOST_CHECK_EQUAL(
      server_stdout_handle->str(), "CIRCUIT\nCIRCUIT READY\nENDCIRCUIT\n");
  BOOST_CHECK(results->str().find("INGESTION") != string::npos);
}
