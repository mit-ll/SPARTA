//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        For manipulating TA1 and TA3 schema information. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 12 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_COMMON_SCHEMA_H_
#define CPP_COMMON_SCHEMA_H_

#include <mysql/mysql.h>
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <set>

#include "check.h"

/// A field is identified by a table, field_name pair. Inheritied from pair so we
/// get operators <, <=, ==, >, >=.
class FieldId : public std::pair<std::string, std::string> {
 public:
  FieldId(const std::string& table, const std::string& field)
      : std::pair<std::string, std::string>(table, field) {}

  const std::string& table() const { return first; }
  const std::string& field() const { return second; }
};

struct FieldInfo {
  FieldInfo(enum_field_types t, int m, bool i, bool u)
      : type(t), max_length(m), index(i), unsigned_flag(u) {}
  enum_field_types type;
  /// max_length is only meaningful for text, char, varchar, and blob types.
  int max_length;
  /// If true, the contents of this fields should be added to the keywords and
  /// stems index table to support CONTAINED_IN and CONTAINS_STEM queries.
  bool index;
  bool unsigned_flag;
};

/// For SPAR the TA1 baseline needs to be aware of the schema. For example, for
/// TA1 the insert command is just a list of values. It is assumed that the
/// client knows the fields, their order, their type, etc. so it can match the
/// values to the field names. This simple class parses the .csv file we use to
/// communicate the schema to the test harness and clients and has accessor
/// methods for determinig the name and type of any field.
///
/// Note that this parses a file that is different from the one delivered to
/// performers as this reflects the layout of the fields in our baseline and the
/// data types we've chosen for the baseline.
class Schema {
 public:
  /// Construct a Schema object from an istream (normally an open .csv file)
  /// contaiing the field names in the standard SPAR format.
  Schema(std::istream* schema_data);

  /// Returns the number of field/table pairs. Thus, if a single field appears in
  /// two tables that counts twice towards Size().
  size_t Size() const {
    return field_info_.size();
  }

  /// Similar to Size(), but the is the number of fields not field/table pairs.
  /// Thus, if a field appears in two tables this only counts once.
  size_t NumFields() const {
    return fields_in_order_.size();
  }

  /// Return the FieldId for the i^th field. Note that there may be more than one
  /// as some fields (e.g. primary keys) can appear in more than one table.
  const std::vector<FieldId>* GetFieldIds(size_t i) const;

  /// Return the FieldIds for the field named field_name. If that field is in
  /// just a single table this returns just a single result, but if the field
  /// appears in multiple tables this will return all of them.
  const std::vector<FieldId>* GetFieldIdsForField(
      const std::string& field_name) const;

  /// enum_field_types is defined in mysql.h
  enum_field_types GetFieldType(const FieldId& field_id) const;

  const FieldInfo& GetFieldInfo(const FieldId& field_id) const;

  const std::set<std::string>& GetAllTables() const {
    return all_tables_;
  }

  const std::vector<FieldId>& GetFieldsInTable(
      const std::string& table) const {
    DCHECK(table_to_fields_.find(table) != table_to_fields_.end());
    return table_to_fields_.at(table);
  }

  /// Returns true if the field type requires quoting when part of an SQL
  /// statment, and false otherwise
  bool RequiresQuotes(const FieldInfo& f_info) const {
    return quoted_types_->find(f_info.type) != quoted_types_->end();
  }

  /// Returns true if the field needs to be escaped before being added to an SQL
  /// statement and false otherwise.
  bool RequiresEscaping(const FieldInfo& f_info) const {
    return escaped_types_->find(f_info.type) != escaped_types_->end();
  }

  /// Returns whether the schema contained any fields with indexing enabled
  bool RequiresIndex() {
    return requires_index_;
  }

 private:
  /// We need to know the *order* of the fields as INSERT commands just send the
  /// data assuming it matches the order of the schema file.
  std::vector<std::vector<FieldId> > fields_in_order_;
  /// Info for each field.
  std::map<FieldId, FieldInfo> field_info_;

  /// map from field name to the a set of fieldIds (one for each table in which
  /// the field appears).
  std::map<std::string, std::vector<FieldId> > field_name_to_ids_;

  /// A set of the unique table names.
  std::set<std::string> all_tables_;

  /// A map from table name to the fields in that table. We could clearly store
  /// just the field name instead of the FiledId here but this makes it easier to
  /// retrieve info about each field and such.
  std::map<std::string, std::vector<FieldId> > table_to_fields_;

  /// Indicates whether any columns in the schema have indexing enabled.
  bool requires_index_;

  /// Static map from the string used in the CSV file to represent a field type
  /// to the value from the MySQL enum_field_types.
  static std::map<std::string, enum_field_types>* field_type_str_enum_map_;
  /// Static set of field types that require quoting
  static std::set<enum_field_types>* quoted_types_;
  /// Static set of field types that need to be escaped
  static std::set<enum_field_types>* escaped_types_;
  friend void InitializeSchemaStatics();
  friend void FinalizeSchemaStatics();
};

#endif
