// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A string-like data structure that is faster for some
//                     operations (like append and substring).
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 06 Aug 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_KNOT_H_
#define CPP_COMMON_KNOT_H_

#include <boost/shared_ptr.hpp>
#include <ostream>
#include <string>

#include "knot-impl/knot-node-deque.h"
#include "knot-iterator.h"

/// A string-like class that is much faster at certain operations. Knots consist
/// of multiple "strands". Each strand is a sub-string but may be held in a
/// std::string, a char*, etc.
///
/// Each of the methods below has its run time documented assuming the total
/// length of the string in the knot is n characters and that the knot contains m
/// strands.
class Knot {
 public:
  /// Default constructor.
  Knot();
  /// Constructor. Takes ownership of data, a string containing length
  /// characters.
  Knot(const char* data, size_t length);
  /// Constructor. Takes ownership of the data.
  Knot(const std::string* data);
  /// Copy constructor.
  Knot(const Knot& other) : knot_deque_(other.knot_deque_) {}

  virtual ~Knot();

  typedef _KnotIterator_ iterator;
  friend class _KnotIterator_;

  /// Appends the strand to the knot. This takes ownership of data. This takes
  /// O(1) time.
  void Append(Strand* data);
  /// Appends the string in data, whose size is given by length, to the knot.
  /// Takes ownership of data. This takes O(1) time.
  void Append(const char* data, size_t length);
  /// Appends all the data in other to this knot. If other has k strands this is
  /// an O(k) operation.
  void Append(const Knot& other);
  /// Appends a std::string*. This takes ownership of the string. This is an O(1)
  /// operation.
  void Append(const std::string* data);
  /// Appends a char* that this knot does *not* own. The caller owns the data and
  /// will guarantee that the data remains valid for the life of the Knot. The
  /// most common use case is string literals in code.
  void AppendOwned(const char* data, size_t length);

  /// Make this equal to the empty Knot. This is an O(m) operation as the
  /// reference counts to all strands must be decrimented and, if necessary, the
  /// strands must be freed.
  void Clear();

  /// Copy the data in the knot to output. This is an O(n) operation.
  virtual void ToString(std::string* output) const;
  /// The same as above but returns the string instead of copying into a passed
  /// string. Note that this may involve extra copies if the compiler is unable
  /// to perform return-value optimizations.
  std::string ToString() const;

  /// Returns the number of characters in the string.
  size_t Size() const;

  typedef boost::shared_ptr<KnotNodeDeque> SharedKnotDeque;
  
  /// Returns an iterator pointing to the character or end() if not
  /// found.
  iterator Find(char to_find) const;

  /// Same as the above but starts searching at the start_it position. It's is
  /// important to note that a valid, non end(),  Knot::iterator is *not*
  /// invalidated by a call to Append(). Thus you can do a Find(), call
  /// LastCharIter(), call Append(), increment that iterator and then do another
  /// find from that point forward.  This is very helpful with code that
  /// repeatedly concatenates strings and looks for a delimiter.
  iterator Find(char to_find, iterator start_it) const;

  /// STL-compatible iterator methods for character-wise iteration.
  iterator begin() const { return iterator(0, 0, this); }
  iterator end() const { return iterator(-1, -1, this); }
  /// Returns an iterator pointing to the last character in the Knot.
  iterator LastCharIter() const;
  /// Returns at iterator pointing at the char_idx^th character in the knot
  /// (0-indexed). This is an O(log(m)) operation.
  iterator IteratorForChar(int char_idx) const;

  /// Assignment operator. This is O(1) as all this does is share a reference to
  /// the underlying data. However, the next Append (or other write) operation
  /// causes a copy-on-write and is thus O(m).
  Knot& operator=(const Knot& other) {
    knot_deque_ = other.knot_deque_;
    return *this;
  }

  /// Returns true if the first length characters in the Knot are equal to
  /// other, and false otherwise. This is O(k) where k == length.
  bool StartsWith(const char* other, size_t length) const;
  /// Returns true if the 1st other.size() characters are the same as the
  /// characters in other. Note that other may contain '\0' or other binary
  /// characters. O(other.size()).
  bool StartsWith(const std::string& other) const {
    return StartsWith(other.data(), other.size());
  }

  /// Returns true if this knot holds the same characters as other. O(length)
  bool Equal(const char* other, size_t length) const {
    return (Size() == length) && (StartsWith(other, length));
  }

  /// Compares this knot to the given string for character-by-character equality.
  /// Note: we intentionally didn't create a version of this for char* array's as
  /// that's potentially costly: you'd have to call strlen() to get the length of
  /// the array which requires traversing the entire array even if we could
  /// discover that the strings aren't equal just by looking at the first
  /// character.
  bool operator==(const std::string& other) const {
    return (Size() == other.size()) && (StartsWith(other));
  }

  bool operator!=(const std::string& other) const {
    return !(*this == other);
  }

  /// Creates a subnot that starts at start (inclusive) and ends at end
  /// (exclusive). O(k) where k is the number of strands between start_it and
  /// end_it.
  Knot SubKnot(iterator start_it, iterator end_it) const;

  /// Removes all the characters from the front of the Knot up to, but not
  /// including, up_to_iter. O(k) where k is the number of strands to be removed.
  void LeftErase(iterator up_to_iter);

  /// Returns a knot == SubKnot(this->begin(), split_point) and changes this knot
  /// so that we've essentially called LeftErase(split_point). Thus, it splits
  /// the knot into two parts.
  /// TODO(njhwang) This is currently not very intuitive, as it includes the
  /// separator in the original knot. It makes it very awkward to use like one
  /// would normally use a split function.
  Knot Split(iterator split_point) {
    Knot result = SubKnot(begin(), split_point);
    LeftErase(split_point);
    return result;
  }

  /// Writes the knot to an ostream. Note that operator<< is also defined below.
  void WriteToStream(std::ostream& output) const;

  /// Write the knot to a file descriptor. If writing the entire knot would cause
  /// the write to block returns an iterator to the 1st character that was *not*
  /// written. If all the data was written returns end().
  ///
  /// NOTE: This assumes the file descriptor has had O_NONBLOCK set on it so that
  /// it will not block!
  iterator WriteToFileDescriptor(int file_descriptor) const {
    return WriteToFileDescriptor(file_descriptor, begin());
  }
 
  /// The same as the above, but tries to write all the data between start_it and
  /// end(). Generally this is used after a call to WriteToFileDescriptor() above
  /// returns something other than end() in order to write the rest of the Knot.
  iterator WriteToFileDescriptor(int file_descriptor, iterator start_it) const;

  /// Writes to file_descriptor until all the data has been written blocking as
  /// necessary. This assumes O_NONBLOCK is *not* set on it.
  void BlockingWriteToFileDescriptor(int file_descriptor) const;

 private:
  /// For constructing sub-knots.
  Knot(SharedKnotDeque knot_deque);
  /// Pointer to the underlying data.
  SharedKnotDeque knot_deque_;
};

inline std::ostream& operator<<(std::ostream& stream, const Knot& knot) {
  knot.WriteToStream(stream);
  return stream;
}

#endif
