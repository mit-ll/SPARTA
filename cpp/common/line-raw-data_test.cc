//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for LineRawData 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 12 Sep 2012   omd            Original Version
//*****************************************************************

#include "line-raw-data.h"

#define BOOST_TEST_MODULE LineRawDataTest
#include "test-init.h"

#include <sstream>
#include <string>

#include "knot.h"
#include "types.h"

using namespace std;

// Make sure the basic getter/setter methods work when the data type is Knot.
BOOST_AUTO_TEST_CASE(BasicMethodsWorkKnot) {
  LineRawData<Knot> lrd;

  lrd.AddRaw(Knot(new string("Raw Data")));
  lrd.AddLine(Knot(new string("Line 1")));
  lrd.AddLine(Knot(new string("Line 2")));
  lrd.AddRaw(Knot(new string("aa")));

  BOOST_REQUIRE_EQUAL(lrd.Size(), 4);

  BOOST_CHECK_EQUAL(lrd.IsRaw(0), true);
  BOOST_CHECK_EQUAL(lrd.Get(0), "Raw Data");

  BOOST_CHECK_EQUAL(lrd.IsRaw(1), false);
  BOOST_CHECK_EQUAL(lrd.Get(1), "Line 1");

  BOOST_CHECK_EQUAL(lrd.IsRaw(2), false);
  BOOST_CHECK_EQUAL(lrd.Get(2), "Line 2");

  BOOST_CHECK_EQUAL(lrd.IsRaw(3), true);
  BOOST_CHECK_EQUAL(lrd.Get(3), "aa");
}

// Same as the above, but using SharedData as DataT
BOOST_AUTO_TEST_CASE(BasicMethodsWorkShardData) {
  LineRawData<SharedData> lrd;

  lrd.AddRaw(SharedData(new string("Raw Data")));
  lrd.AddLine(SharedData(new string("Line 1")));
  lrd.AddLine(SharedData(new string("Line 2")));
  lrd.AddRaw(SharedData(new string("aa")));

  BOOST_REQUIRE_EQUAL(lrd.Size(), 4);

  BOOST_CHECK_EQUAL(lrd.IsRaw(0), true);
  BOOST_CHECK_EQUAL(*lrd.Get(0), "Raw Data");

  BOOST_CHECK_EQUAL(lrd.IsRaw(1), false);
  BOOST_CHECK_EQUAL(*lrd.Get(1), "Line 1");

  BOOST_CHECK_EQUAL(lrd.IsRaw(2), false);
  BOOST_CHECK_EQUAL(*lrd.Get(2), "Line 2");

  BOOST_CHECK_EQUAL(lrd.IsRaw(3), true);
  BOOST_CHECK_EQUAL(*lrd.Get(3), "aa");

}

// Make sure the LineRawOutput method of the Knot class works as expected.
BOOST_AUTO_TEST_CASE(LineRawOutputWorksKnot) {
  LineRawData<Knot> lrd;

  lrd.AddRaw(Knot(new string("Raw Data")));
  lrd.AddLine(Knot(new string("Line 1")));
  lrd.AddLine(Knot(new string("Line 2")));
  lrd.AddRaw(Knot(new string("aa")));
  
  BOOST_CHECK_EQUAL(lrd.LineRawOutput(),
                    "RAW\n"
                    "8\n"
                    "Raw Data"
                    "ENDRAW\n"
                    "Line 1\n"
                    "Line 2\n"
                    "RAW\n"
                    "2\n"
                    "aa"
                    "ENDRAW\n");
}

BOOST_AUTO_TEST_CASE(LineRawDataFromFileWorks) {
  istringstream f1(
    "Line 1\n"
    "Line 2\n"
    "RAW\n"
    "10\n"
    "aaaaaaaaaa"
    "ENDRAW\n"
    "Line 3\n"
    "RAW\n"
    "2\n"
    "om"
    "ENDRAW\n");
  LineRawData<Knot> d1;
  LineRawDataFromFile(&f1, &d1); 

  BOOST_REQUIRE_EQUAL(d1.Size(), 5);
  BOOST_CHECK_EQUAL(d1.IsRaw(0), false);
  BOOST_CHECK_EQUAL(d1.Get(0), "Line 1");
  BOOST_CHECK_EQUAL(d1.IsRaw(1), false);
  BOOST_CHECK_EQUAL(d1.Get(1), "Line 2");
  BOOST_CHECK_EQUAL(d1.IsRaw(2), true);
  BOOST_CHECK_EQUAL(d1.Get(2), "aaaaaaaaaa");
  BOOST_CHECK_EQUAL(d1.IsRaw(3), false);
  BOOST_CHECK_EQUAL(d1.Get(3), "Line 3");
  BOOST_CHECK_EQUAL(d1.IsRaw(4), true);
  BOOST_CHECK_EQUAL(d1.Get(4), "om");
}

BOOST_AUTO_TEST_CASE(LineRawDataFromFileMultipleByteCountsWorks) {
  istringstream f1(
    "Line 1\n"
    "RAW\n"
    "10\n"
    "aaaaaaaaaa"
    "2\n"
    "xx"
    "ENDRAW\n"
    "RAW\n"
    "2\n"
    "om"
    "3\n"
    "bza"
    "ENDRAW\n");
  LineRawData<Knot> d1;
  LineRawDataFromFile(&f1, &d1); 

  BOOST_REQUIRE_EQUAL(d1.Size(), 3);
  BOOST_CHECK_EQUAL(d1.IsRaw(0), false);
  BOOST_CHECK_EQUAL(d1.Get(0), "Line 1");
  BOOST_CHECK_EQUAL(d1.IsRaw(1), true);
  BOOST_CHECK_EQUAL(d1.Get(1), "aaaaaaaaaaxx");
  BOOST_CHECK_EQUAL(d1.IsRaw(2), true);
  BOOST_CHECK_EQUAL(d1.Get(2), "ombza");
}

BOOST_AUTO_TEST_CASE(OffsetsWork) {
  LineRawData<Knot> d;
  // Create a LRD with "Line 0\nLine 1\n..."
  for (int i = 0; i < 10; ++i) {
    ostringstream data;
    data << "Line " << i;
    d.AddLine(Knot(new string(data.str())));
  }

  BOOST_CHECK_EQUAL(d.Get(0), "Line 0");
  BOOST_CHECK_EQUAL(d.Size(), 10);
  BOOST_CHECK_EQUAL(d.LineRawOutput(),
                    "Line 0\nLine 1\nLine 2\nLine 3\nLine 4\n"
                    "Line 5\nLine 6\nLine 7\nLine 8\nLine 9\n");

  d.SetStartOffset(2);
  BOOST_CHECK_EQUAL(d.Size(), 8);
  BOOST_CHECK_EQUAL(d.Get(0), "Line 2");
  BOOST_CHECK_EQUAL(d.LineRawOutput(),
                    "Line 2\nLine 3\nLine 4\n"
                    "Line 5\nLine 6\nLine 7\nLine 8\nLine 9\n");

  d.SetEndOffset(3);
  BOOST_CHECK_EQUAL(d.Size(), 5);
  BOOST_CHECK_EQUAL(d.Get(0), "Line 2");
  BOOST_CHECK_EQUAL(d.LineRawOutput(),
                    "Line 2\nLine 3\nLine 4\nLine 5\nLine 6\n");

  // Make sure the offset is relative to the current ones.
  d.SetStartOffset(1);
  BOOST_CHECK_EQUAL(d.Size(), 4);
  BOOST_CHECK_EQUAL(d.Get(0), "Line 3");
  BOOST_CHECK_EQUAL(d.LineRawOutput(),
                    "Line 3\nLine 4\nLine 5\nLine 6\n");
}

// Make sure offsets work with Raw data as well as line data.
BOOST_AUTO_TEST_CASE(OffsetWorksWithRaw) {
  LineRawData<Knot> d;
  d.AddLine(Knot(new string("Line 1")));
  d.AddRaw(Knot(new string("Line 2")));
  d.AddRaw(Knot(new string("Line 3")));
  d.AddLine(Knot(new string("Line 4")));
  d.AddRaw(Knot(new string("Line 5")));

  BOOST_CHECK_EQUAL(d.Size(), 5);
  BOOST_CHECK_EQUAL(d.IsRaw(0), false);
  BOOST_CHECK_EQUAL(d.IsRaw(1), true);
  BOOST_CHECK_EQUAL(d.IsRaw(2), true);
  BOOST_CHECK_EQUAL(d.IsRaw(3), false);
  BOOST_CHECK_EQUAL(d.IsRaw(4), true);

  BOOST_CHECK_EQUAL(d.Get(0), "Line 1");
  BOOST_CHECK_EQUAL(d.Get(1), "Line 2");

  d.SetStartOffset(2);
  BOOST_CHECK_EQUAL(d.Size(), 3);
  BOOST_CHECK_EQUAL(d.IsRaw(0), true);
  BOOST_CHECK_EQUAL(d.IsRaw(1), false);
  BOOST_CHECK_EQUAL(d.IsRaw(2), true);
  BOOST_CHECK_EQUAL(d.Get(0), "Line 3");
  BOOST_CHECK_EQUAL(d.Get(1), "Line 4");
  BOOST_CHECK_EQUAL(d.Get(2), "Line 5");

  d.SetEndOffset(1);
  BOOST_CHECK_EQUAL(d.Size(), 2);
  BOOST_CHECK_EQUAL(d.IsRaw(0), true);
  BOOST_CHECK_EQUAL(d.IsRaw(1), false);
  BOOST_CHECK_EQUAL(d.Get(0), "Line 3");
  BOOST_CHECK_EQUAL(d.Get(1), "Line 4");

  // And make sure offsets are cumulative
  d.SetEndOffset(1);
  BOOST_CHECK_EQUAL(d.Size(), 1);
  BOOST_CHECK_EQUAL(d.IsRaw(0), true);
  BOOST_CHECK_EQUAL(d.Get(0), "Line 3");
}
