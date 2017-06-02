//*****************************************************************
//
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Class for handling mixed UTF-8 line and binary raw data 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 03 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_LINE_RAW_DATA_H_
#define CPP_COMMON_LINE_RAW_DATA_H_

#include <iostream>
#include <sstream>
#include <vector>

#include "check.h"
#include "knot.h"
#include "string-algo.h"

/// This class is for handling a mixture of line mode and raw mode data.
/// Typically a protocol extension will simply buffer up all the received data
/// in a LineRawData object and then process it from there. Example usage:
///
/// LineRawData<string> lrd;
///
/// // Typically this would be done by a protocol extension to buffer up all the
/// // data it received.
/// lrd.AddLine("Line 1");
/// lrd.AddRaw("Raw 1");
/// lrd.AddLine("Line 2");
///
/// Now the data can be retrieved with Get and its type determined with IsRaw.
/// CHECK(lrd.IsRaw(0) == false);
/// CHECK(lrd.IsRaw(1) == true);
/// CHECK(lrd.IsRaw(2) == false);
///
/// CHECK(lrd.Get(0) == "Line 1");
/// CHECK(lrd.Get(1) == "Raw 1");
/// CHECK(lrd.Get(2) == "Line 2");
/// 
/// CHECK(lrd.Size() == 3);
///
/// The template parameter determines the data type that should hold the stored
/// lines and raw data (usually either SharedData (which is
/// boost::shared_ptr<string>), or Knot). Note that the destructor doesn't free
/// anything so DataT either needs to be a type that takes care of its own
/// memory or you need to specialize the template to create a destructor that
/// will free things.

template<class DataT>
class LineRawData {
 public:
  LineRawData() : start_offset_(0), end_offset_(0) {}
  /// Constructs a LineRawData containing the given data. If is_raw is true the
  /// data is treated as a raw array of bytes. Note that by using the
  /// string(const char* s, size_t n) string constructor you can create a string
  /// that contains an arbitrary array of bytes, including the '\0' character.
  LineRawData(DataT data, bool is_raw);
  virtual ~LineRawData() {}

  /// Add the given line (which should not contain the terminating '\n') to the
  /// data stored here. This takes ownership of line.
  void AddLine(DataT line);

  /// Add the bytes in data to the data stored here. This takes ownership of
  /// data.
  void AddRaw(DataT data);

  /// Returns a LineRawProtocol formatted string that represents the data stored
  /// in this object. This is specialized for DataT == Knot. If you need this for
  /// other values of DataT you will need to write a different specialization.
  Knot LineRawOutput() const;

  /// Like the above, but appends the LineRawOutput to the passed Knot instead of
  /// creating a new one.
  void AppendLineRawOutput(Knot* output) const;

  /// Returns the i^th data item.
  DataT Get(unsigned int i) const;

  /// Indicates if the i^th data item is raw or line data.
  bool IsRaw(unsigned int i) const;

  /// The number of data items in this structure.
  size_t Size() const {
    return data_.size() - start_offset_ - end_offset_;
  }

  /// In much of our code a handler of some kind receives a LineRawData as
  /// input.  It needs to strip off the outer layer (e.g. COMMAND/ENDCOMMAND or
  /// INSERT/ENDINSERT) and pass the rest to the next handler in "the stack".
  /// To make this easy to do without copying anything you can call
  /// SetStartOffset and SetEndOffset. All following Get() commands will be
  /// relative to this offset. For example, after calling SetStartOffset(1),
  /// Size() will return 1 less than it would have before the call and Get(0)
  /// will return the same thing that Get(1) would have returned before the
  /// call. Similarly for SetEndOffset.
  ///
  /// Note that further calls ot SetXOffset are relative to existing offsets.
  /// Thus, calling SetStartOffset(1) followed by SetStartOffset(3) has the
  /// same effect as calling SetStartOffset(4) once.
  ///
  /// The user can not call AddLine or AddRaw after calling these method. They
  /// make the data immutable.
  void SetStartOffset(size_t offset);
  void SetEndOffset(size_t offset);

 private:
  /// Array of the data stored by this object.
  std::vector<DataT> data_;
  /// if raw_indicators_[i] is true then data_[i] is raw data. Otherwise
  /// data_[i] is UTF-8 line-mode data.
  std::vector<bool> raw_indicators_;  
  /// See comments above SetStartOffset and SetEndOffset
  size_t start_offset_;
  size_t end_offset_;
};

/// Function to construct a LineRawData<Knot> from the contents of a file.
void LineRawDataFromFile(std::istream* file, LineRawData<Knot>* output);
Knot GetRawData(std::istream* file);

////////////////////////////////////////////////////////////////////////////////
// Template method definitions.
////////////////////////////////////////////////////////////////////////////////

template<class DataT>
LineRawData<DataT>::LineRawData(DataT data, bool is_raw)
    : start_offset_(0), end_offset_(0) {
  if (is_raw) {
    AddRaw(data);
  } else {
    AddLine(data);
  }
}

template<class DataT>
void LineRawData<DataT>::AddLine(DataT line) {
  DCHECK(start_offset_ == 0 && end_offset_ == 0);
  CHECK(data_.size() == raw_indicators_.size());
  data_.push_back(line);
  raw_indicators_.push_back(false);
  CHECK(data_.size() == raw_indicators_.size());
}

template<class DataT>
void LineRawData<DataT>::AddRaw(DataT data) {
  DCHECK(start_offset_ == 0 && end_offset_ == 0);
  CHECK(data_.size() == raw_indicators_.size());
  data_.push_back(data);
  raw_indicators_.push_back(true);
  CHECK(data_.size() == raw_indicators_.size());
}

template<class DataT>
DataT LineRawData<DataT>::Get(unsigned int i) const {
  CHECK(i < Size());
  return data_[i + start_offset_];
}

template<class DataT>
void LineRawData<DataT>::SetStartOffset(size_t offset) {
  CHECK(offset <= Size());
  start_offset_ += offset; 
}

template<class DataT>
void LineRawData<DataT>::SetEndOffset(size_t offset) {
  CHECK(offset <= Size());
  end_offset_ += offset; 
}

template<class DataT>
bool LineRawData<DataT>::IsRaw(unsigned int i) const {
  CHECK(i < Size());
  return raw_indicators_[i + start_offset_];
}

template<>
inline void LineRawData<Knot>::AppendLineRawOutput(Knot* output) const {
  for (unsigned int i = 0; i < Size(); ++i) {
    Knot next_out = Get(i);
    if (IsRaw(i)) {
      std::string* header_string = new std::string("RAW\n");
      *header_string += itoa(next_out.Size());
      *header_string += "\n";
      output->Append(header_string);
      output->Append(next_out);
      static const char kEndRawStr[] = "ENDRAW\n";
      static const int kEndRawStrLen = strlen(kEndRawStr);
      output->AppendOwned(kEndRawStr, kEndRawStrLen);
    } else {
      output->Append(next_out);
      output->AppendOwned("\n", 1);
    }
  }
}

template<>
inline Knot LineRawData<Knot>::LineRawOutput() const {
  Knot output;
  AppendLineRawOutput(&output);
  return output;
}

#endif
