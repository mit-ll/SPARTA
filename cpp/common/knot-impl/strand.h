//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Definition of a Strand, the small strings that make up a
//                     JRope 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Jul 2012   omd            Original Version
//*****************************************************************


#ifndef COMMON_JROPE_STRAND_H_
#define COMMON_JROPE_STRAND_H_

#include <boost/shared_array.hpp>
#include <boost/shared_ptr.hpp>
#include <cstdlib>
#include <ostream>
#include <sstream>
#include <string>

/// This is the base class for Strand. We can have multiple types of strands so
/// that a Knot can be a mix of multiple sources of data. We'll clearly want
/// subclasses for char* and std::string, but note that this can be far more
/// flexible. For example, we could have Strands the refer to files on disk so
/// that you could mix data on the disk with in-memory data.
class Strand {
 public:
  virtual ~Strand() {}
  /// Must *quickly* return the character at offset in the strand. The Knot
  /// assumes this is a constant time operation.
  virtual const char* PtrToCharAt(size_t offset) const = 0;
  /// Generally doesn't need to be overridden.
  virtual char CharAt(size_t offset) const {
    return *PtrToCharAt(offset);
  }
  /// Returns the size of the strand. This too should be constant time.
  virtual int Size() const = 0;
  /// Writes the strand to the output stream
  virtual void WriteToStream(std::ostream& stream) const = 0;
  /// Returns a sub-strand consisting of the length characters starting at
  /// character offset. If length is npos return the entire strand starting from
  /// offset.
  virtual Strand* GetSubstrand(int offset, size_t length) const = 0;
  /// May be inefficient but handy for unit tests and such.
  std::string ToString() const {
    std::ostringstream value;
    WriteToStream(value);
    return value.str();
  }

  /// Returns a pointer to a char* holding the data. Note that this array is
  /// *not* NULL terminated. Most strand types can do this in O(1) time.
  virtual const char* ToCharPtr() const = 0;

  /// Return a copy of this strand. This should be fast, generally the copy
  /// shares the same underlying data.
  virtual Strand* Copy() const = 0;

  /// Returns the index of to_find in the strand or Strand::npos if the character
  /// wasn't found.
  ///
  /// TODO(odain) Right now all subclasses can override this in a more efficient
  /// way. We could provide a default version that uses CharAt for classes that
  /// can't be more efficient.
  virtual size_t Find(char to_find) const = 0;

  /// Same as the above but starts searching at start_idx.
  virtual size_t Find(char to_find, size_t start_idx) const = 0;

  /// Returns true if the length characters starting at offset equal the first
  /// length characters in other.
  virtual bool EqualRange(
      const char* other, int offset, size_t length) const = 0;

  /// Mimicking std::string::npos this is used to indicate that you want all the
  /// characters when asking for a substring.
  static const size_t npos;

  /// The position of the 1st character of this strand relative to the first
  /// character in it's underlying data store. 
  virtual size_t StartOffset() const = 0;
};

////////////////////////////////////////////////////////////////////////////////
// CharStrandBase
////////////////////////////////////////////////////////////////////////////////

/// We have at least two types of strands that "really" get their data from a
/// char*. One really *is* just a char* array, and the other is a BPBuffer. This
/// class could also be used as a wrapper around stl string buffers as those too
/// hold the data in an underlying char* array.
///
/// This implements most of the necessary functionality using the pure virtual
/// method GetArray(). Thus subclasses need only arrange to store the necessary
/// object (a shared pointer to a BPBuffer or a char* for example), implement
/// GetArray() and GetSubstrnd.
class CharStrandBase : public Strand {
 public:
  /// Strand that holds the 1st length characters returned by GetArray().
  CharStrandBase(size_t length);
  /// Holds the 1st length characters beginning at character start in the data
  /// returned by GetArray().
  CharStrandBase(size_t start, size_t length);
  virtual ~CharStrandBase() {}

  virtual const char* PtrToCharAt(size_t offset) const;
  virtual int Size() const {
    return end_ - start_;
  }

  virtual void WriteToStream(std::ostream& stream) const {
    stream.write(GetArray() + start_, Size());
  }

  virtual Strand* GetSubstrand(int offset, size_t length) const = 0;

  virtual Strand* Copy() const = 0;

  virtual size_t Find(char to_find) const;

  virtual size_t Find(char to_find, size_t start_idx) const;

  virtual bool EqualRange(
      const char* other, int offset, size_t length) const;

  virtual size_t StartOffset() const { return start_; }

  virtual const char* ToCharPtr() const { return GetArray() + start_; }

 protected:
  /// Return the *base* array, without start_ taken into account.
  virtual const char* GetArray() const = 0;

 private:
  size_t start_;
  size_t end_;

};

////////////////////////////////////////////////////////////////////////////////
// CharPtrStrand
////////////////////////////////////////////////////////////////////////////////


typedef boost::shared_array<const char> SharedCharPtr;

/// A Strand that takes its data from an array of characters.
class CharPtrStrand : public CharStrandBase {
 public:
  /// Construct a strand that holds the 1st length characters in data. This takes
  /// ownership of data.
  CharPtrStrand(const char* data, size_t length)
      : CharStrandBase(length), data_(data) {
  }
  /// Construct a strand that holds the 1st length characters of data starting at
  /// start. This takes ownership of *all of* data even though only part of it is
  /// used.
  CharPtrStrand(SharedCharPtr data, size_t start, size_t length)
      : CharStrandBase(start, length), data_(data) {
  }

  virtual ~CharPtrStrand() {}

  virtual Strand* GetSubstrand(int offset, size_t length) const;

  virtual Strand* Copy() const {
    return new CharPtrStrand(data_, StartOffset(), Size());
  }

 protected:
  virtual const char* GetArray() const {
    return data_.get();
  }

 private:
  SharedCharPtr data_;
};

////////////////////////////////////////////////////////////////////////////////
// OwnedCharPtrStrand
////////////////////////////////////////////////////////////////////////////////


/// A strand that takes its data from a char* that it does *not* own. This is
/// thus not responsible for ensuring the lifetime of the data or ensuring that
/// the data ever gets freed. This is particularly useful for string literals in
/// source code whose lifetime == the lifetime of the entire program.
class OwnedCharPtrStrand : public CharStrandBase {
 public:
  OwnedCharPtrStrand(const char* data, size_t length)
      : CharStrandBase(length), data_(data) {
  }

  OwnedCharPtrStrand(const char* data, size_t start, size_t length)
      : CharStrandBase(start, length), data_(data) {
  }

  virtual ~OwnedCharPtrStrand() {}

  virtual Strand* GetSubstrand(int offset, size_t length) const;

  virtual Strand* Copy() const {
    return new OwnedCharPtrStrand(data_, StartOffset(), Size());
  }

 protected:
  virtual const char* GetArray() const {
    return data_;
  }

 private:
  const char* data_;
};

////////////////////////////////////////////////////////////////////////////////
// StringStrand
////////////////////////////////////////////////////////////////////////////////


typedef boost::shared_ptr<const std::string > SharedString;

/// A Strand that takes its data from a std::string
class StringStrand : public CharStrandBase {
 public:
  StringStrand(const std::string* data)
      : CharStrandBase(data->size()), data_(data) {}
  StringStrand(SharedString data, size_t start, size_t length)
      : CharStrandBase(start, length), data_(data) {}

  virtual ~StringStrand() {}

  virtual Strand* GetSubstrand(int offset, size_t length) const;

  virtual Strand* Copy() const {
    return new StringStrand(data_, StartOffset(), Size());
  }

 protected:
  virtual const char* GetArray() const {
    return data_->data();
  } 

 private:
 SharedString data_;
};


#endif
