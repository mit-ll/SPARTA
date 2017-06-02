//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of LineRawParser
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 02 July 2012   omd            Original Version
//*****************************************************************

#include "line-raw-parser.h"

#include <cstdlib>
#include <cstring>

#include "logging.h"
#include "check.h"

using std::string;

const char kRawDelimiter[] = "RAW";
const int kRawDelimiterSize = strlen(kRawDelimiter);
const char kEndRawDelimiter[] = "ENDRAW";
const int kEndRawDelimiterSize = strlen(kEndRawDelimiter);



LineRawParser::LineRawParser(LineRawParseHandler* parse_handler)
    : parse_handler_(parse_handler), raw_mode_(NULL), cur_mode_(LINE) {
  line_search_position_ = cur_data_.end();
}

void LineRawParser::DataReceived(Strand* data) {
  cur_data_.Append(data);
  DCHECK(cur_data_.Size() > 0);

  // Alternate between line mode and raw mode as long as either indicates there
  // may be more data to parse. If the raw_mode_ pointer isn't NULL we're in raw
  // mode.
  bool keep_going = true;
  while (keep_going) {
    if (cur_mode_ == LINE) {
      keep_going = LineMode();
    } else {
      keep_going = raw_mode_->ParseLoop();
      if (cur_mode_ != RAW) {
        raw_mode_.reset(NULL);
      }
    }
  }
}

void LineRawParser::RawModeDone() {
  cur_mode_ = LINE;
}

bool LineRawParser::GetLine(Knot* line) {
  if (cur_data_.Size() == 0) {
    return false;
  }

  if (line_search_position_ == cur_data_.end()) {
    line_search_position_ = cur_data_.begin();
  } else {
    ++line_search_position_;
  }

  Knot::iterator lf_it = cur_data_.Find('\n', line_search_position_);
  if (lf_it != cur_data_.end()) {
    *line = cur_data_.SubKnot(cur_data_.begin(), lf_it);
    // We don't want to keep the '\n' character so advance past that and then
    // erase everything to the left. If that leaves the string empty, just call
    // Clear() on the knot.
    ++lf_it;
    if (lf_it == cur_data_.end()) {
      cur_data_.Clear();
    } else {
      cur_data_.LeftErase(lf_it);
    }
    line_search_position_ = cur_data_.end();
    return true;
  } else {
    line_search_position_ = cur_data_.LastCharIter();
    return false;
  }
}

bool LineRawParser::GetBytes(size_t byte_count, Knot* result) {
  if (cur_data_.Size() < byte_count) {
    return false;
  }

  if (cur_data_.Size() == byte_count) {
    *result = cur_data_;
    cur_data_.Clear();
  } else {
    Knot::iterator split_it = cur_data_.IteratorForChar(byte_count);
    *result = cur_data_.Split(split_it);
  }
  return true;
}

bool LineRawParser::UnparsedData() const {
  return cur_data_.Size() > 0;
}

bool LineRawParser::LineMode() {
  Knot line;
  bool line_found = GetLine(&line);
  while (line_found) {
    if (line.Equal(kRawDelimiter, kRawDelimiterSize)) {
      cur_mode_ = RAW;
      raw_mode_.reset(new RawModeParser(this));
      return UnparsedData();
    } else {
      parse_handler_->LineReceived(line);
      line_found = GetLine(&line);
    }
  }
  return false;
}

////////////////////////////////////////////////////////////////////////////////
// RawModeParser
////////////////////////////////////////////////////////////////////////////////

const size_t UNKNOWN_BYTE_COUNT = 0;

RawModeParser::RawModeParser(LineRawParser* parent)
    : byte_count_(UNKNOWN_BYTE_COUNT), data_(), parent_(parent) {
}

// Keep looking for byte count/data pairs until we receive ENDRAW
bool RawModeParser::ParseLoop() {
  while (true) {
    if (byte_count_ == UNKNOWN_BYTE_COUNT) {
      // We're waiting for a line that indicates how many bytes to expect.
      Knot count_line;
      if (!parent_->GetLine(&count_line)) {
        // We haven't yet received a complete count line. For example, if the
        // byte count is going to be 100 we may have only received "10" and
        // we're still waiting on "0\n". Since there's nothing left in the
        // buffer we return false, indicating there's no more parsable data, and
        // we wait for the next call to DataReceived().
        return false;
      } else if (count_line.Equal(kEndRawDelimiter, kEndRawDelimiterSize)) {
        // Pass the raw data we received to the user's callback.
        parent_->parse_handler_->RawReceived(data_);
        // Exit raw mode and return.
        parent_->RawModeDone();
        return parent_->UnparsedData();
      } else {
        char* end_ptr;
        CHECK(count_line.Size() > 0) << "Missing byte size in raw mode.";
        string count_str;
        count_line.ToString(&count_str);
        byte_count_ = strtol(count_str.c_str(), &end_ptr, 10);
        CHECK(*end_ptr == '\0') << "Invalid raw mode count: " << count_line;
        if (byte_count_ < 0) {
          LOG(FATAL) << "Negative raw mode byte count found: "
              << count_line;
        }
      }
    } else {
      // We know how many bytes to expect. As soon as the required bytes show up
      // append them to data_ (or put them in data_ if data_ is empty). As most
      // users send all the data in a single byte count/data chunk we usually
      // avoid all data copies here as we simply wrap the data pointer in a
      // SharedPointer without making any copies.
      Knot new_data;
      if (!parent_->GetBytes(byte_count_, &new_data)) {
        return false;
      } else {
        byte_count_ = UNKNOWN_BYTE_COUNT;
        data_.Append(new_data);
      }
    }
  }
}
