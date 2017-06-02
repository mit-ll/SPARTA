#include "line-raw-parser.h"

#define BOOST_TEST_MODULE LineRawParserTest

#include <cstring>
#include <string>
#include <vector>

#include "check.h"
#include "string-algo.h"
#include "test-init.h"

using namespace std;

class StoreLines : public LineRawParseHandler {
 public:
  virtual void LineReceived(Knot data) {
    lines.push_back(data.ToString());
  }
  virtual void RawReceived(Knot data) {
    raw.push_back(data.ToString());
  }
  vector<string> lines;
  vector<string> raw;
};

// Builds a strand from a single, '\0'-terminated char*
Strand* GetStrand(const char* data) {
  return new CharPtrStrand(StrDup(data), strlen(data));
}

// Builds a strand from a std::string. This makes it easy to create a strind
// from raw data as a string can easily handle that.
Strand* GetStrand(const string& data) {
  char* str_copy = new char[data.size()];
  data.copy(str_copy, data.size());
  return new CharPtrStrand(str_copy, data.size());
}

BOOST_AUTO_TEST_CASE(OneLineAtATimeWorks) {
  StoreLines* store_lines = new StoreLines;
  LineRawParser parser(store_lines);

  parser.DataReceived(GetStrand("Line 1\n"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 1);
  BOOST_CHECK_EQUAL(store_lines->lines[0], "Line 1");

  parser.DataReceived(GetStrand("Line 2\n"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 2);
  BOOST_CHECK_EQUAL(store_lines->lines[1], "Line 2");
  BOOST_CHECK_EQUAL(store_lines->raw.size(), 0);
}

BOOST_AUTO_TEST_CASE(MultipleLinesWork) {
  StoreLines* store_lines = new StoreLines;
  LineRawParser parser(store_lines);

  parser.DataReceived(GetStrand("Line 1\nLine 2\nLine 3\n"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 3);
  BOOST_CHECK_EQUAL(store_lines->lines[0], "Line 1");
  BOOST_CHECK_EQUAL(store_lines->lines[1], "Line 2");
  BOOST_CHECK_EQUAL(store_lines->lines[2], "Line 3");

  parser.DataReceived(GetStrand("Line 4\nLine 5\n"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 5);
  BOOST_CHECK_EQUAL(store_lines->lines[3], "Line 4");
  BOOST_CHECK_EQUAL(store_lines->lines[4], "Line 5");
  BOOST_CHECK_EQUAL(store_lines->raw.size(), 0);
}

BOOST_AUTO_TEST_CASE(LineSplitOverInputsWorks) {
  StoreLines* store_lines = new StoreLines;
  LineRawParser parser(store_lines);

  parser.DataReceived(GetStrand("Li"));
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);

  parser.DataReceived(GetStrand("ne 1"));
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);

  parser.DataReceived(GetStrand("\n"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 1);
  BOOST_CHECK_EQUAL(store_lines->lines[0], "Line 1");

  parser.DataReceived(GetStrand("Line"));
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 1);

  parser.DataReceived(GetStrand(" 2\n"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 2);
  BOOST_CHECK_EQUAL(store_lines->lines[1], "Line 2");
  BOOST_CHECK_EQUAL(store_lines->raw.size(), 0);
}

BOOST_AUTO_TEST_CASE(ComplexLinesWork) {
  StoreLines* store_lines = new StoreLines;
  LineRawParser parser(store_lines);

  parser.DataReceived(GetStrand("Line 1\nLi"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 1);
  BOOST_CHECK_EQUAL(store_lines->lines[0], "Line 1");

  parser.DataReceived(GetStrand("ne 2\nLine 3\nLine 4"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 3);
  BOOST_CHECK_EQUAL(store_lines->lines[1], "Line 2");
  BOOST_CHECK_EQUAL(store_lines->lines[2], "Line 3");

  parser.DataReceived(GetStrand("\n"));
  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 4);
  BOOST_CHECK_EQUAL(store_lines->lines[3], "Line 4");
  BOOST_CHECK_EQUAL(store_lines->raw.size(), 0);
}

// Check that raw mode, when the "RAW", data, and "ENDRAW" arrives all at once
// works.
BOOST_AUTO_TEST_CASE(SimpleRawWorks) {
  StoreLines* store_lines = new StoreLines;
  LineRawParser parser(store_lines);

  // Construct raw1, the raw data is the 10 bytes: 0, 1, ..., 9
  string raw1 = "RAW\n10\n";
  const int raw1_size = 10;
  char raw_d1[raw1_size] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
  raw1 += string(raw_d1, raw1_size);
  raw1 += "ENDRAW\n";

  parser.DataReceived(GetStrand(raw1));
  BOOST_REQUIRE_EQUAL(store_lines->raw.size(), 1);
  BOOST_REQUIRE_EQUAL(store_lines->raw[0].size(), raw1_size);
  // Since the raw data contains embedded '\0' characters we can't just
  // BOOST_CHECK_EQUAL as that would treat the raw as a C-string and stop at the
  // '\0' character.
  for (int i = 0; i < raw1_size; ++i) {
    BOOST_CHECK_EQUAL(store_lines->raw[0][i], i);
  }

  // Similar to the above but send the data in two byte-count/data pairs. Also,
  // construct the data to be difficult by embedding '\0' and '\n' characters.
  string raw2 = "RAW\n7\n";
  const int raw2_p1_size = 7;
  char raw2_p1_d[raw2_p1_size] = {'\n', 'b', '\0', 111, '\n', 'Z', '@'};
  const int raw2_p2_size = 5;
  char raw2_p2_d[raw2_p2_size] = {'\n', '\0', 'a', '\n', '\n'};
  raw2 += string(raw2_p1_d, raw2_p1_size);
  raw2 += "5\n";
  raw2 += string(raw2_p2_d, raw2_p2_size);
  raw2 += "ENDRAW\n";
  parser.DataReceived(GetStrand(raw2));
  BOOST_REQUIRE_EQUAL(store_lines->raw.size(), 2);
  // Even though the data was sent in two chunks the callback should only be
  // called once per RAW/ENDRAW pair. Check that all the data from both chunks
  // was received.
  BOOST_REQUIRE_EQUAL(store_lines->raw[1].size(), raw2_p1_size + raw2_p2_size);
  for (int i = 0; i < raw2_p1_size; ++i) {
    BOOST_CHECK_EQUAL(store_lines->raw[1][i], raw2_p1_d[i]);
  }
  for (int i = raw2_p1_size; i < raw2_p1_size + raw2_p2_size; ++i) {
    BOOST_CHECK_EQUAL(store_lines->raw[1][i], raw2_p2_d[i - raw2_p1_size]);
  }
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);
}

// Construct some raw data that's split over multiple inputs and make sure it
// still parses correctly.
BOOST_AUTO_TEST_CASE(RawSplitWorks) {
  StoreLines* store_lines = new StoreLines;
  LineRawParser parser(store_lines);

  parser.DataReceived(GetStrand("RA"));
  BOOST_CHECK_EQUAL(store_lines->raw.size(), 0);
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);

  parser.DataReceived(GetStrand("W\n1"));
  BOOST_CHECK_EQUAL(store_lines->raw.size(), 0);
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);

  const int raw1_size = 10;
  const char raw1[raw1_size] = {'\n', 2, 3, 4, 5, 6, 7, '\0', 'a', '\n'};
  // We send the "1" above so now we send the "0\n" indicating 10 bytes. We then
  // send the 1st 3 of the ten bytes.
  string s1 = "0\n";
  s1 += string(raw1, 3);
  parser.DataReceived(GetStrand(s1));
  BOOST_CHECK_EQUAL(store_lines->raw.size(), 0);
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);

  // Send the remaining 7 bytes plus "ENDR"
  string s2 =  string(raw1 + 3, 7);
  s2 += "ENDR";
  parser.DataReceived(GetStrand(s2));
  BOOST_CHECK_EQUAL(store_lines->raw.size(), 0);
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);

  parser.DataReceived(GetStrand("AW\n"));
  BOOST_REQUIRE_EQUAL(store_lines->raw.size(), 1);
  BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);
  BOOST_REQUIRE_EQUAL(store_lines->raw[0].size(), raw1_size);
  for (int i = 0; i < raw1_size; ++i) {
    BOOST_CHECK_EQUAL(store_lines->raw[0][i], raw1[i]);
  }
}

// Construct a RAW/ENDRAW string with 2 chunks of data. Split that into 3
// sub-strings in every possible way and make sure they all parse the same way.
BOOST_AUTO_TEST_CASE(RawAllSplitsWork) {
  // The data is "RAW\n7\n" then 7 bytes of raw data (in raw_p1_d) then "5\n"
  // then 5 bytes of raw data (in raw_p2_d) then "ENDRAW\n"
  string raw_str("RAW\n7\n");
  const int raw_p1_size = 7;
  char raw_p1_d[raw_p1_size] = {'\n', 'b', '\0', 127, '\n', 'Z', '@'};
  const int raw_p2_size = 12;
  char raw_p2_d[raw_p2_size] = {'\n', '\0', 'a', '\n', '\n', 118, 126, 103,
    '\0', 0, 1, '\r'};
  raw_str += string(raw_p1_d, raw_p1_size);
  raw_str += "12\n";
  raw_str += string(raw_p2_d, raw_p2_size);
  raw_str += "ENDRAW\n";

  // Construct 3 strings. The fist string is s1 bytes long and s1_bytes will
  // vary between 1 and the lengths of the string - 2 (-2 so the other 2 strings
  // can be at least one byte each). s2 will be s2_bytes long between 1 and the
  // length of the string - the length of s1 - 1 (-1 to leave room for the last
  // string), etc.
  for (size_t s1_bytes = 1; s1_bytes < raw_str.size() - 2; ++s1_bytes) {
    for (size_t s2_bytes = 1;
         s2_bytes < raw_str.size() - s1_bytes - 1; ++s2_bytes) {
      size_t s3_bytes = raw_str.size() - s1_bytes - s2_bytes;
      CHECK(s3_bytes > 0);
      CHECK(s3_bytes < raw_str.size());
      CHECK(s1_bytes + s2_bytes + s3_bytes == raw_str.size());

      string s1(raw_str, 0, s1_bytes);
      BOOST_CHECK_EQUAL(s1.size(), s1_bytes);
      string s2(raw_str, s1_bytes, s2_bytes);
      BOOST_CHECK_EQUAL(s2.size(), s2_bytes);
      string s3(raw_str, s1_bytes + s2_bytes, string::npos);
      BOOST_CHECK_EQUAL(s3.size(), s3_bytes);

      StoreLines* store_lines = new StoreLines;
      LineRawParser parser(store_lines);

      parser.DataReceived(GetStrand(s1));
      parser.DataReceived(GetStrand(s2));
      parser.DataReceived(GetStrand(s3));

      BOOST_REQUIRE_EQUAL(store_lines->raw.size(), 1);
      BOOST_REQUIRE_EQUAL(store_lines->raw[0].size(),
                          raw_p1_size + raw_p2_size);
      // Check that the recieved data is the concatenation of raw_p1_d and
      // raw_p2_d.
      for (int i = 0; i < raw_p1_size; ++i) {
        BOOST_CHECK_EQUAL(store_lines->raw[0][i], raw_p1_d[i]);
      }
      for (int i = raw_p1_size; i < raw_p1_size + raw_p2_size; ++i) {
        BOOST_CHECK_EQUAL(store_lines->raw[0][i],
                          raw_p2_d[i - raw_p1_size]);
      }
      BOOST_CHECK_EQUAL(store_lines->lines.size(), 0);
    }
  }
}

BOOST_AUTO_TEST_CASE(LineRawMixedWorks) {
  StoreLines* store_lines = new StoreLines;
  LineRawParser parser(store_lines);

  parser.DataReceived(GetStrand("Line 1\n"));
  parser.DataReceived(GetStrand("RAW\n3\nabcENDRAW\n"));
  parser.DataReceived(GetStrand("Line 2\n"));
  parser.DataReceived(GetStrand("Line 3\nRAW\n2\ndeENDRAW\nLine 4\n"));

  BOOST_REQUIRE_EQUAL(store_lines->lines.size(), 4);
  BOOST_REQUIRE_EQUAL(store_lines->raw.size(), 2);

  BOOST_CHECK_EQUAL(store_lines->lines[0], "Line 1");
  BOOST_CHECK_EQUAL(store_lines->lines[1], "Line 2");
  BOOST_CHECK_EQUAL(store_lines->lines[2], "Line 3");
  BOOST_CHECK_EQUAL(store_lines->lines[3], "Line 4");

  BOOST_CHECK_EQUAL(store_lines->raw[0].size(), 3);
  BOOST_CHECK_EQUAL(store_lines->raw[0], "abc");
  BOOST_CHECK_EQUAL(store_lines->raw[1].size(), 2);
  BOOST_CHECK_EQUAL(store_lines->raw[1], "de");
}

