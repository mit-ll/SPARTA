//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Base class for all TA3.1 metadata fields 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Jan 2013   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA3_FIELDS_FIELD_BASE_H_
#define CPP_TEST_HARNESS_TA3_FIELDS_FIELD_BASE_H_

#include <memory>
#include <set>
#include <string>

#include "common/knot.h"

/// To generate publications and subscriptions we need to be able to get random
/// values for each field. In many instances we also need to be able to do that
/// but excluding some set of values. This is the base class for all fields. It
/// is fairly minimal, just providing a name (mostly just for debugging purposes
/// and nicer error messages), and the ability to get random values from the
/// field.
///
/// Note that a FieldBase is really a field *and* it's distribution. We might use
/// different FieldBase subclasses for the same logical field in different
/// applications in the same executable. For example, when generating tests with
/// low match rates the fname field might have uniformly distributed values with
/// a small domain and when testing high match rates it might have a non-uniform
/// distribution with much higher match rates.
class FieldBase {
 public:
  /// Constructor. name indicates the name of the field (e.g. fname, address,
  /// income, etc.)
  FieldBase(const std::string& name, const std::string& type) : 
    name_(name), type_(type) {}
  virtual ~FieldBase() {}

  /// Return the name of the field.
  std::string name() const { return name_; }
  std::string type() const { return type_; }

  /// Set the seed used by the random generators fro RandomValueX below.
  virtual void SetSeed(int seed) = 0;

  /// Generates a random value for the field and puts it in the char* array
  /// pointed to by output. max_char is the maximum number of characters that may
  /// be put in the array. This should always be >= MaxLength(). The only reason
  /// to have the user pass it is so we can double-check that we're not going to
  /// overflow the buffer.
  ///
  /// This returns a pointer to the first character *after* the appended value
  /// (i.e. it returns output + length of the generated value). Note that this
  /// does *not* null-terminate the string (because we often want to build up a
  /// CSV representation of the metadata by concatenating such values.)
  virtual char* RandomValue(size_t max_char, char* output) const = 0;
  /// Like the above but guarantees that the generated value will not be in the
  /// set exclude.
  virtual char* RandomValueExcluding(
      const std::set<std::string>& exclude,
      size_t max_char, char* output) const = 0;
  /// Same as the above, but appends to the passed string instead of a char*
  void RandomValueExcluding(const std::set<std::string>& exclude,
                            std::string* output) const {
    char buffer[MaxLength()];
    char* res_end = RandomValueExcluding(exclude, MaxLength(), buffer);
    output->append(buffer, res_end - buffer);
  }

  /// The maximum number of characters in any value this field could generate
  /// when RandomValue is called.
  virtual size_t MaxLength() const = 0;

  /// Returns the number of unique values.
  virtual int NumValues() const = 0;

 private:
  std::string name_;
  std::string type_;
};

#endif
