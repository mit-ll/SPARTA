//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for LineRawToOutputHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 May 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE ObjectThreadsTest

#include <sstream>
#include <string>

#include "line-raw-to-output-handler.h"
#include "test-init.h"

using namespace std;

BOOST_AUTO_TEST_CASE(CheckBasic) {
  stringstream output;

  const char raw_data[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
  const string raw_data_str(raw_data, 10);
  const char raw_data2[] = {'a', 'b', '\0', 127};
  const string raw_data2_str(raw_data2, 4);


  OutputHandler* handler = OutputHandler::GetHandler(&output);
  LineRawToOutputHandler lro(handler);
  lro.Start();
  lro.Line("Line 1");
  lro.Line("Line 2");
  lro.Raw(raw_data_str);
  lro.Line("Line 3");
  lro.Raw(raw_data2_str);
  lro.Stop();
  
  stringstream expected;
  expected << "Line 1\nLine 2\nRAW\n10\n" << raw_data_str
           << "ENDRAW\nLine 3\nRAW\n4\n"
           << raw_data2_str << "ENDRAW\n";

  BOOST_CHECK_EQUAL(output.str(), expected.str());
}

BOOST_AUTO_TEST_CASE(LinePartWorks) {
  stringstream output;
  OutputHandler* handler = OutputHandler::GetHandler(&output);
  LineRawToOutputHandler lro(handler);
  lro.Start();
  lro.LinePart("Line ").LinePart(11).LinePart(" EOL").LineDone();
  lro.Stop();

  BOOST_CHECK_EQUAL(output.str(), "Line 11 EOL\n");
}
