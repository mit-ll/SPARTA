//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of BindManager and subclasses 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 Oct 2012   omd            Original Version
//*****************************************************************

#include "bind-manager.h"

#include <string>
#include <vector>

using std::string;
using std::vector;

////////////////////////////////////////////////////////////////////////////////
// BindManager
////////////////////////////////////////////////////////////////////////////////

BindManager* BindManager::GetBindManager(
      enum_field_types field_type, bool unsigned_flag, int max_length, 
      MYSQL_BIND* bind_struct) {
  switch (field_type) {
    case MYSQL_TYPE_BLOB:
      return new BlobBindManager(max_length, bind_struct);
      break;
    case MYSQL_TYPE_VAR_STRING:
      return new VarStringBindManager(max_length, bind_struct);
      break;
    case MYSQL_TYPE_STRING:
      return new StringBindManager(max_length, bind_struct);
      break;
    case MYSQL_TYPE_TINY:
      // TODO(njhwang) currently can't get string-algo's ConvertString working with
      // int8_t, so just using int16_t for now
      if (unsigned_flag) {
        return new IntegerBindManager<uint16_t>(field_type, bind_struct);
      } else {
        return new IntegerBindManager<int16_t>(field_type, bind_struct);
      }
      break;
    case MYSQL_TYPE_SHORT:
      if (unsigned_flag) {
        return new IntegerBindManager<uint16_t>(field_type, bind_struct);
      } else {
        return new IntegerBindManager<int16_t>(field_type, bind_struct);
      }
      break;
    case MYSQL_TYPE_LONG:
      if (unsigned_flag) {
        return new IntegerBindManager<uint32_t>(field_type, bind_struct);
      } else {
        return new IntegerBindManager<int32_t>(field_type, bind_struct);
      }
      break;
    case MYSQL_TYPE_LONGLONG:
      if (unsigned_flag) {
        return new IntegerBindManager<uint64_t>(field_type, bind_struct);
      } else {
        return new IntegerBindManager<int64_t>(field_type, bind_struct);
      }
      break;
    case MYSQL_TYPE_DATE:
      return new DateBindManager(bind_struct);
      break;
    default:
      LOG(FATAL) << "Unknown field type: " << field_type;
      return NULL;
  }
}

////////////////////////////////////////////////////////////////////////////////
// NonNullBindManager
////////////////////////////////////////////////////////////////////////////////

const my_bool NonNullBindManager::is_null_ = false;

NonNullBindManager::NonNullBindManager(enum_field_types field_type,
                                       MYSQL_BIND* bind_struct) {
  memset(bind_struct, 0, sizeof(MYSQL_BIND));
  bind_struct->buffer_type = field_type;
  // Const-cast is justified as MySQL lib won't modify it but they didn't
  // declare it const.
  bind_struct->is_null = const_cast<my_bool*>(&is_null_);
}

////////////////////////////////////////////////////////////////////////////////
// StringLikeBindManager
////////////////////////////////////////////////////////////////////////////////

StringLikeBindManager::StringLikeBindManager(
    enum_field_types type, int max_length, MYSQL_BIND* bind_struct)
    : NonNullBindManager(type, bind_struct), bind_struct_(bind_struct) {
  // The docs are *very* unclear about if this is the max length or just the
  // length. I *think* it's the max length (the length goes in the length field
  // but I guess it could duplicate the info).
  bind_struct_->buffer_length = max_length;
  bind_struct_->length = &data_length_;
}

void StringLikeBindManager::Bind(const Knot& data) {
  data.ToString(&data_string_);
  // The const-cast is unavoidable since MySQL requires a void* not a const
  // void*. However, it doesn't modify the data so this is safe.
  bind_struct_->buffer = const_cast<char*>(data_string_.data());
  data_length_ = data_string_.size();
}

////////////////////////////////////////////////////////////////////////////////
// DateBindManager
////////////////////////////////////////////////////////////////////////////////

DateBindManager::DateBindManager(MYSQL_BIND* bind_struct)
    : NonNullBindManager(MYSQL_TYPE_DATE, bind_struct) {
  // This seems strange, but the examples on the MySQL site sets this to 0 and
  // NULL so that's what I'm doing.
  bind_struct->buffer_length = 0;
  bind_struct->length = NULL;
  bind_struct->buffer = &time_data_;
}

void DateBindManager::Bind(const Knot& data) {
  string date_str;
  data.ToString(&date_str);
  vector<string> date_parts;
  Split(date_str, '-', &date_parts);
  CHECK(date_parts.size() == 3)
      << date_str << " is not a valid date.";

  time_data_.year = SafeAtoi(date_parts[0]);
  CHECK(time_data_.year > 0);
  CHECK(time_data_.year < 3000);

  time_data_.month = SafeAtoi(date_parts[1]);
  CHECK(time_data_.month > 0);
  CHECK(time_data_.month <= 12);

  time_data_.day = SafeAtoi(date_parts[2]);
  CHECK(time_data_.day > 0);
  CHECK(time_data_.day < 32);
}
