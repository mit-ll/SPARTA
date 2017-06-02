//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit test for the publish script
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "publish-script.h"

#define BOOST_TEST_MODULE PublishScriptTest
#include "common/test-init.h"
#include "common/test-util.h"

#include <boost/assign/list_of.hpp>
#include <boost/thread.hpp>
#include <boost/bind.hpp>
#include <iostream>

#include "publish-script.h"
#include "test-harness/ta3/commands/publish-command.h"
#include "test-harness/common/numbered-command-fixture.h"
#include "test-harness/common/delay-generators.h"
#include "common/general-logger.h"
#include "common/util.h"

using namespace std;
using boost::assign::list_of;

class PublishScriptTestFixture : public NumberedCommandFixture {
 public:
  PublishScriptTestFixture();

  virtual ~PublishScriptTestFixture() {}

  PublishCommand publish_command;
};

PublishScriptTestFixture::PublishScriptTestFixture()
    : publish_command(nc_extension) {
}

BOOST_FIXTURE_TEST_CASE(PublishScriptWorks, PublishScriptTestFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  sut_output_stream << "READY" << endl;

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  istringstream* publications_file = new istringstream(
  "METADATA\n"
  "TABATHA,DELEON,805395315,1947-11-24,364 State Hwy Y,Jacksonville,Missouri,65260,Female,White,Never_Married,Not_In_School,Yes_Naturalized,0,Never_Active_Duty,SPANISH,12,10\n"
  "METADATA\n"
  "IRMA,GILGER,423143576,2009-02-19,475 Vega Verde,Laughlin A F B,Texas,78840,Female,White,Never_Married,Not_In_School,Yes_Born_In_US,0,Under_17,ITALIAN,0,52\n"
  "METADATA\n"
  "MICHAEL,CHOUDHARY,564039216,1982-11-06,150 Sherwood Ln,Guy,Arkansas,72061,Male,Asian,Married,Not_In_School,Yes_Born_In_US,9000,Never_Active_Duty,SPANISH,0,52\n"
  "METADATA\n"
  "MICHAEL,CHOUDHARY,564039216,1982-11-06,150 Sherwood Ln,Guy,Arkansas,72061,Male,Asian,Married,Not_In_School,Yes_Born_In_US,9000,Never_Active_Duty,SPANISH,0,52\n");

  TruncatedPoissonNumGenerator rng(100, 0);
  PublishScript script(publications_file, &ZeroDelay, 
                       &publish_command, &logger, 0, rng);
  boost::thread script_thread(
      boost::bind(&PublishScript::Run, &script));

  VerifyIStreamContents(list_of(string("COMMAND 0"))("PUBLISH")("METADATA")
    (string("TABATHA,DELEON,805395315,1947-11-24,364 State Hwy Y,") + 
     "Jacksonville,Missouri,65260,Female,White,Never_Married,Not_In_School," +
     "Yes_Naturalized,0,Never_Active_Duty,SPANISH,12,10")("PAYLOAD")("RAW"),
    &sut_input_stream);
  string actual_content;
  getline(sut_input_stream, actual_content);
  LOG(DEBUG) << "Payload has " << actual_content << " bytes";
  getline(sut_input_stream, actual_content);
  LOG(DEBUG) << "Payload contents (including ENDRAW): " << actual_content;
  VerifyIStreamContents(list_of(string("ENDPAYLOAD"))("ENDPUBLISH")("ENDCOMMAND"),
    &sut_input_stream);

  // There shouldn't be another command, no matter how long I wait, until I send
  // results for the first one. Even if I send a READY.
  sut_output_stream << "READY" << endl;
  boost::this_thread::sleep(boost::posix_time::milliseconds(100));
  BOOST_CHECK_EQUAL(sut_input_stream.rdbuf()->in_avail(), 0);
  LOG(DEBUG) << "Sent READY";

  sut_output_stream << "RESULTS 0\n"
      "DONE\n"
      "ENDRESULTS" << endl;
  LOG(DEBUG) << "Sent RESULTS";

  VerifyIStreamContents(list_of(string("COMMAND 1"))("PUBLISH")("METADATA")
    (string("IRMA,GILGER,423143576,2009-02-19,475 Vega Verde,Laughlin A F B,") +
     "Texas,78840,Female,White,Never_Married,Not_In_School,Yes_Born_In_US,0," +
     "Under_17,ITALIAN,0,52")("PAYLOAD")("RAW"), &sut_input_stream);
  getline(sut_input_stream, actual_content);
  LOG(DEBUG) << "Payload has " << actual_content << " bytes";
  getline(sut_input_stream, actual_content);
  LOG(DEBUG) << "Payload contents (including ENDRAW): " << actual_content;
  VerifyIStreamContents(list_of(string("ENDPAYLOAD"))("ENDPUBLISH")("ENDCOMMAND"),
    &sut_input_stream);

  sut_output_stream << "READY" << endl;
  boost::this_thread::sleep(boost::posix_time::milliseconds(100));
  BOOST_CHECK_EQUAL(sut_input_stream.rdbuf()->in_avail(), 0);

  sut_output_stream << "RESULTS 1\n"
      "DONE\n"
      "ENDRESULTS" << endl;

  VerifyIStreamContents(list_of(string("COMMAND 2"))("PUBLISH")("METADATA")
    (string("MICHAEL,CHOUDHARY,564039216,1982-11-06,150 Sherwood Ln,Guy,") +
     "Arkansas,72061,Male,Asian,Married,Not_In_School,Yes_Born_In_US,9000," +
     "Never_Active_Duty,SPANISH,0,52")("PAYLOAD")("RAW"), &sut_input_stream);
  getline(sut_input_stream, actual_content);
  LOG(DEBUG) << "Payload has " << actual_content << " bytes";
  getline(sut_input_stream, actual_content);
  LOG(DEBUG) << "Payload contents (including ENDRAW): " << actual_content;
  VerifyIStreamContents(list_of(string("ENDPAYLOAD"))("ENDPUBLISH")("ENDCOMMAND"),
    &sut_input_stream);

  sut_output_stream << "READY" << endl;
  boost::this_thread::sleep(boost::posix_time::milliseconds(100));
  BOOST_CHECK_EQUAL(sut_input_stream.rdbuf()->in_avail(), 0);

  sut_output_stream << "RESULTS 2\n"
      "DONE\n"
      "ENDRESULTS" << endl;

  VerifyIStreamContents(list_of(string("COMMAND 3"))("PUBLISH")("METADATA")
    (string("MICHAEL,CHOUDHARY,564039216,1982-11-06,150 Sherwood Ln,Guy,") +
     "Arkansas,72061,Male,Asian,Married,Not_In_School,Yes_Born_In_US,9000," +
     "Never_Active_Duty,SPANISH,0,52")("PAYLOAD")("RAW"), &sut_input_stream);
  getline(sut_input_stream, actual_content);
  LOG(DEBUG) << "Payload has " << actual_content << " bytes";
  getline(sut_input_stream, actual_content);
  LOG(DEBUG) << "Payload contents (including ENDRAW): " << actual_content;
  VerifyIStreamContents(list_of(string("ENDPAYLOAD"))("ENDPUBLISH")("ENDCOMMAND"),
    &sut_input_stream);
  LOG(DEBUG) << "Verified final input stream contents";

  sut_output_stream << "READY" << endl;
  LOG(DEBUG) << "Sent final READY";
  boost::this_thread::sleep(boost::posix_time::milliseconds(100));
  BOOST_CHECK_EQUAL(sut_input_stream.rdbuf()->in_avail(), 0);
  LOG(DEBUG) << "Verified input stream empty";

  sut_output_stream << "RESULTS 3\n"
      "DONE\n"
      "ENDRESULTS" << endl;
  LOG(DEBUG) << "Sent final RESULTS";
  
  script_thread.join();
  LOG(DEBUG) << "Joined test thread";
}
