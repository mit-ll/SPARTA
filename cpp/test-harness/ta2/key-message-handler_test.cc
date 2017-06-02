#include <sstream>
#include "key-message-handler.h"
#include "stream-util.h"

#define BOOST_TEST_MODULE 
#define BOOST_TEST_DYN_LINK

#include <boost/test/unit_test.hpp>
#include "common/test-init.h"
using namespace std;

BOOST_AUTO_TEST_CASE(KeyHandlerWorks) {

  // Mimics the SUT client's stdin
  stringstream* client_stdin_pipe = new stringstream();
  // Mimics the SUT client's stdout
  stringstream* client_stdout_pipe = new stringstream();
  // Mimics the SUT server's stdin
  stringstream* server_stdin_pipe = new stringstream();
  // Mimics the SUT server's stdout
  stringstream* server_stdout_pipe = new stringstream();

  unique_ptr<stringstream> client_stdin_ptr(client_stdin_pipe);
  unique_ptr<stringstream> client_stdout_ptr(client_stdout_pipe);
  unique_ptr<stringstream> server_stdin_ptr(server_stdin_pipe);
  unique_ptr<stringstream> server_stdout_ptr(server_stdout_pipe);
  unique_ptr<stringstream> results(new stringstream());

  TestHarnessIStream client_stdout(move(client_stdout_ptr));
  TestHarnessOStream client_stdin(move(client_stdin_ptr));
  TestHarnessIStream server_stdout(move(server_stdout_ptr));
  TestHarnessOStream server_stdin(move(server_stdin_ptr));
  
  auto k = KeyMessageHandler(results.get());
  k.set_client_stdin(&client_stdin);
  k.set_client_stdout(&client_stdout);
  k.set_server_stdin(&server_stdin);
  k.set_server_stdout(&server_stdout);

  // Write the expected client response. This is done before the client actually
  // gets the securit parameter but for testing that's okay. Ideally, the
  // client's response is run in a separate thread.
  *client_stdout_pipe << "KEY\npublic_key\nENDKEY" << endl;

  stringstream file;
  file << "security parameters";
  k.Send(&file);

  BOOST_CHECK_EQUAL(
      client_stdin_pipe->str(), "KEY\nsecurity parameters\nENDKEY\n");
  BOOST_CHECK_EQUAL(
      client_stdout_pipe->str(), "KEY\npublic_key\nENDKEY\n");
  BOOST_CHECK_EQUAL(
      server_stdin_pipe->str(), "KEY\npublic_key\nENDKEY\n");
  BOOST_CHECK(results->str().find("KEYGEN") != string::npos);
}
