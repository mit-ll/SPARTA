#include <sstream>
#include "stream-util.h"

#define BOOST_TEST_MODULE 
#define BOOST_TEST_DYN_LINK

#include <boost/test/unit_test.hpp>
#include "common/test-init.h"

using namespace std;

BOOST_AUTO_TEST_CASE(TestHarnessOStreamWorks) {

  stringstream* sut = new stringstream();
  unique_ptr<ostream> ofs(sut);
  TestHarnessOStream output_stream(move(ofs));
  stringstream* log = new stringstream();
  unique_ptr<ostream> logger(log);
  output_stream.SetDebugLogStream(move(logger), true);
  
  output_stream.Write("HELLO");
  output_stream.Write("WORLD");
  const char* buf = "Hello World";
  output_stream.Write(buf, 11);

  BOOST_CHECK_EQUAL(sut->str(), "HELLO\nWORLD\nHello World");
  BOOST_CHECK_EQUAL(log->str(), "HELLO\nWORLD\nHello World");
}

BOOST_AUTO_TEST_CASE(TestHarnessIStreamWorks) {

  stringstream* sut = new stringstream();
  stringstream* log = new stringstream();
      

  *sut << "FOO" << endl;
  *sut << "BAR" << endl;
  const char* buf = "Foo bar";
  sut->write(buf, 7);

  unique_ptr<istream> ifs(sut);
  TestHarnessIStream input_stream(move(ifs));
  unique_ptr<ostream> logger(log);
  input_stream.SetDebugLogStream(move(logger), true);

  string line;
  input_stream.Read(&line);
  BOOST_CHECK_EQUAL(line, "FOO");
  input_stream.Read(&line);
  BOOST_CHECK_EQUAL(line, "BAR");
  char input_buf[8];
  input_stream.Read(input_buf, 7);
  input_buf[7] = '\0';
  BOOST_CHECK_EQUAL(buf, "Foo bar");
  
  BOOST_CHECK_EQUAL(log->str(), "FOO\nBAR\nFoo bar");
  
}
