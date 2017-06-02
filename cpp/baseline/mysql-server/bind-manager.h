//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        A class to make it easier to bind data to values for
//                     MySQL prepared statements.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_MYSQL_SERVER_BIND_MANAGER_H_
#define CPP_BASELINE_MYSQL_SERVER_BIND_MANAGER_H_

#include <limits>
#include <mysql/mysql.h>
#include <string>

#include "common/knot.h"
#include "common/string-algo.h"

/// Using MySQL prepared statements is kind of messy. Each data item must be
/// bound to the statement by filling in a MYSQL_BIND structure, and how that's
/// done depends on the type of the data, may involve some local variables to
/// hold things like lengths, etc. To simplify this we use a BindManager for each
/// field that is to be bound to a statement. To use, call GetBindManager for the
/// field you want to bind passing the MYSQL_BIND structure to which you want the
/// data bound (this must be passed as MySQL requires an array of these so we
/// can't make them members of this class). GetBindManager will return an
/// appropriate subclass that knows how to bind this type of data. Then, simply
/// call Bind() on the returned object to get the data converted and bound.
class BindManager {
 public:
  virtual ~BindManager() {}
  virtual void Bind(const Knot& data) = 0;

  static BindManager* GetBindManager(
      enum_field_types field_type, bool unsigned_flag, int max_length, 
      MYSQL_BIND* bind_struct);

 protected:
  BindManager() {}
};

////////////////////////////////////////////////////////////////////////////////
// NonNullBindManager
////////////////////////////////////////////////////////////////////////////////

/// Base class that handles some of the drugery of setting up a BindManager. This
/// can be used as the base class for any BindManager whose value won't be NULL
/// at Bind() time. Note that I've made the constructor so I don't have to
/// declare all sublcasses as friends. Since this is pure virtual (no definition
/// of Bind()) this is safe.
class NonNullBindManager : public BindManager {
 public:
  /// This zeros' out bind_struct, sets its type, and sets its is_null member to
  /// be a pointer to is_null_ == false.
  NonNullBindManager(enum_field_types field_type,
                     MYSQL_BIND* bind_struct);
  virtual ~NonNullBindManager() {}

 private:
  /// We need to pass a *pointer* to a boolean that indicates if it's NULL so
  /// we'll share this one for all bound variables.
  static const my_bool is_null_;
};

////////////////////////////////////////////////////////////////////////////////
// StringLikeBindManager
////////////////////////////////////////////////////////////////////////////////

class BlobBindManager;
class StringBindManager;

/// A base class for BLOB, CHAR, TEXT, etc. as those are almost identical.
class StringLikeBindManager : public NonNullBindManager {
 public:
  virtual ~StringLikeBindManager() {}

  virtual void Bind(const Knot& data);
 private:
  /// Subclasses just need to pass the appropriate field type.
  StringLikeBindManager(enum_field_types type, int max_length,
                       MYSQL_BIND* bind_struct);
  friend class BlobBindManager;
  friend class StringBindManager;
  friend class VarStringBindManager;

  MYSQL_BIND* bind_struct_;
  std::string data_string_;
  /// We need to store a copy of the length outside of the string because MySQL
  /// requires a pointer to an unsigned long holding the length.
  unsigned long data_length_;
};


////////////////////////////////////////////////////////////////////////////////
// BlobBindManager
////////////////////////////////////////////////////////////////////////////////

/// This works for BLOB and TEXT fields
class BlobBindManager : public StringLikeBindManager {
 public:
  virtual ~BlobBindManager() {}

 private:
  BlobBindManager(int max_length, MYSQL_BIND* bind_struct)
      : StringLikeBindManager(MYSQL_TYPE_BLOB, max_length, bind_struct) {}
  friend class BindManager;
};

////////////////////////////////////////////////////////////////////////////////
// StringBindManager
////////////////////////////////////////////////////////////////////////////////

/// This works for CHAR fields
class StringBindManager : public StringLikeBindManager {
 public:
  virtual ~StringBindManager() {}

 private:
  StringBindManager(int max_length, MYSQL_BIND* bind_struct)
      : StringLikeBindManager(MYSQL_TYPE_STRING, max_length, bind_struct) {}
  friend class BindManager;
};

////////////////////////////////////////////////////////////////////////////////
// VarStringBindManager
////////////////////////////////////////////////////////////////////////////////

/// This works for VARCHAR fields
class VarStringBindManager : public StringLikeBindManager {
 public:
  virtual ~VarStringBindManager() {}

 private:
  VarStringBindManager(int max_length, MYSQL_BIND* bind_struct)
      : StringLikeBindManager(MYSQL_TYPE_VAR_STRING, max_length, bind_struct) {}
  friend class BindManager;
};

////////////////////////////////////////////////////////////////////////////////
// IntegerBindManager
////////////////////////////////////////////////////////////////////////////////

/// Templated base class for all integer data types. Subclasses need only call
/// this constructor with the appropriate data type.
template <class NumberType>
class IntegerBindManager : public NonNullBindManager {
 public:
  virtual ~IntegerBindManager() {}

  virtual void Bind(const Knot& data);

 private:
  IntegerBindManager(enum_field_types type, MYSQL_BIND* bind_struct);
  friend class BindManager;

  /// The length of a NumberType variable
  static const unsigned long kTypeLength;
  NumberType data_;
};

////////////////////////////////////////////////////////////////////////////////
// DateBindManager
////////////////////////////////////////////////////////////////////////////////

class DateBindManager : public NonNullBindManager {
 public:
  virtual ~DateBindManager() {}
  virtual void Bind(const Knot& data);

 private:
  DateBindManager(MYSQL_BIND* bind_struct);
  friend class BindManager;

  MYSQL_TIME time_data_;
};

////////////////////////////////////////////////////////////////////////////////
// Template method definitions
////////////////////////////////////////////////////////////////////////////////

template<class NumberType>
const unsigned long IntegerBindManager<NumberType>::kTypeLength =
    sizeof(NumberType);

template<class NumberType>
IntegerBindManager<NumberType>::IntegerBindManager(
    enum_field_types type, MYSQL_BIND* bind_struct)
  : NonNullBindManager(type, bind_struct) {
  bind_struct->buffer_length = kTypeLength;
  /// MySQL won't modify the value so the const-cast is OK
  bind_struct->length = const_cast<unsigned long*>(&kTypeLength);
  bind_struct->is_unsigned = ! std::numeric_limits<NumberType>::is_signed;
  bind_struct->buffer = &data_;
}

template<class NumberType>
void IntegerBindManager<NumberType>::Bind(const Knot& data) {
  std::string data_str;
  data.ToString(&data_str);
  /// Note that on 64-bit platforms a long int and a long long are the same size.
  /// In order for this to be a base class for BigIntBindManager that must be
  /// true so we double-check it here.
  DCHECK(sizeof(long int) == sizeof(long long));
  NumberType result = ConvertString<NumberType>(data_str);
  CHECK(result >= std::numeric_limits<NumberType>::min())
      << data << " is too small for a " << typeid(NumberType).name();
  CHECK(result <= std::numeric_limits<NumberType>::max())
      << data << " is too big for a " << typeid(NumberType).name();
  data_ = result;
}

#endif
