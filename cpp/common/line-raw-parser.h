//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class for parsing LineRaw formatted data
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 02 July 2012   omd            Original Version
//*****************************************************************

#ifndef COMMON_LINE_RAW_PARSER_H_
#define COMMON_LINE_RAW_PARSER_H_

#include <memory>
#include <string>

#include "types.h"
#include "knot.h"

/// Users create a subclass of this and pass it to the LineRawParser
/// constructor.  The LineReceived method will be called for each line of data
/// parsed and the RawReceived method will be called for each chunk of raw data
/// parsed.
class LineRawParseHandler {
 public:
  virtual ~LineRawParseHandler() {}
  virtual void LineReceived(Knot data) = 0;
  virtual void RawReceived(Knot data) = 0;
};

class LineRawParser;

/// This is a friend call of LineRawParser. Raw mode has to maintain a bunch of
/// state so to simplify things we put all that state in here. The
/// LineRawParser then allocates one of these when it enters raw mode and it
/// frees it when it reverts to line mode. That simplifies the code a bit by
/// removing some if's and the need to clear state variables, it also makes the
/// LineRawParser object smaller when there's no raw mode.
class RawModeParser {
 public:
  RawModeParser(LineRawParser* parent);
  /// When this is called all available raw mode data will be parsed. When
  /// "ENDRAW" is encountered parent_->RawModeDone is called to signal that
  /// we're leaving raw mode. This returns true if there's still potentially
  /// parsable data in the LineRawParser buffer and false otherwise.
  bool ParseLoop();

 private:
  /// This either equals UNKNOWN_BYTE_COUNT, indicating we have not yet parsed
  /// out the byte count, or it is the number of bytes we're waiting to receive.
  size_t byte_count_;
  /// The data in raw mode can consist of multiple byte count/data pairs. This
  /// maintains a buffer of all the data bits encountered thus far.
  Knot data_;
  /// The LineRawParser that created this.
  LineRawParser* parent_;
};

/// This is the main parser class. Users should create a subclass of
/// LineRawParseHandler and pass that to the contructor. The DataReceived method
/// is then called for each new bit of data that is to be parsed. The parser
/// handlest the rest.
class LineRawParser {
 public:
  /// This takes ownership of parse_handler and will free it.
  LineRawParser(LineRawParseHandler* parse_handler);
  virtual ~LineRawParser() {}
  /// This takes ownership of data and will either free it or wrap it in a
  /// SharedData and pass it to one of the LineReceived or RawReceived methods
  /// of the parse_handler.
  void DataReceived(Strand* data);
 private:
  /// If possible returns a single line of data from cur_data_ updating
  /// cur_data_ to remove the returned line. If there isn't a complete line of
  /// data in the buffer this returns false.
  bool GetLine(Knot* line);
  /// If possible returns byte_count bytes of data from cur_data_ updating
  /// cur_data_ to remove the returned data. If cur_data_ contains byte_count
  /// bytes of data or more then result will hold this data on return and true
  /// is returned. Otherwise this returns false.
  bool GetBytes(size_t byte_count, Knot* result);
  /// Parses as many line of data as possible out of cur_data_
  bool LineMode();
  /// Called by RawModeParser when ENDRAW is encountered.
  void RawModeDone();
  /// Returns true if there is data left in cur_data_ and false otherwise.
  bool UnparsedData() const;

  friend class RawModeParser;

  /// The user's LineRawParseHandler object. It's LineReceived and RawReceived
  /// methods will be called as appropriate.
  std::auto_ptr<LineRawParseHandler> parse_handler_;
  /// All the data we've encountered but not yet parsed.
  Knot cur_data_;
  Knot::iterator line_search_position_;
  /// Points to a RawModeParser that should be used if if cur_mode_ == RAW.
  std::auto_ptr<RawModeParser> raw_mode_;
  enum ModeType {
    LINE, RAW
  } cur_mode_;
};

#endif
