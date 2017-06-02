//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implemenation of Schema class. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 12 Sep 2012   omd            Original Version
//*****************************************************************

#include "schema.h"

#include <boost/assign/list_inserter.hpp>

#include "statics.h"
#include "string-algo.h"

using std::map;
using std::string;
using std::vector;

Schema::Schema(std::istream* schema_data) {
  // The first line should be a header
  CHECK(schema_data->good());
  string header_line;
  getline(*schema_data, header_line);
  CHECK(header_line.find("name,type,table,length,index") == 0)
      << "Unexpected header line: " << header_line;

  enum PartsIndex {
    kNameIdx = 0, kTypeIdx = 1, kTableIdx = 2,
    kLengthIdx = 3, kIndexIdx = 4
  };
  const size_t kNumFields = 5;

  // Now read the rest of the file. Each line should start with the field name
  // and be comma delimited. size_t only care about the field name, type, and
  // the table holding that so we pull out just that info.
  vector<string> parts;
  while (schema_data->good()) {
    parts.clear();
    string line;
    getline(*schema_data, line);
    if (line.empty()) {
      continue;
    }
    Split(line, ',', &parts);
    CHECK(parts.size() == kNumFields) << "Schema file line does not "
        << "contain expected number of fields:\n" << line;
    // All fields should be non-empty
    for (size_t i = 0; i < kNumFields; ++i) {
      CHECK(parts[i].size() > 0)
          << "Field " << i << " of schema file empty on this line:\n"
          << line;
    }
    // A field (e.g. id) can appear in more than one table. Split the table
    // field on ':' and process the field once for each table.
    vector<string> tables = Split(parts[kTableIdx], ':');
    CHECK(tables.size() > 0);
    vector<FieldId> field_ids;
    for (vector<string>::const_iterator table = tables.begin();
         table != tables.end(); ++table) {
      all_tables_.insert(*table);
      FieldId fid(*table, parts[kNameIdx]);
      field_ids.push_back(fid);
      field_name_to_ids_[parts[kNameIdx]].push_back(fid);

      // Note: there is some repeat work done here if a field is in more than
      // one table. However, most fields aren't and this code isn't at all time
      // critical so it seems better to keep it simple.
      vector<string> type_parts = Split(parts[kTypeIdx], ' ');
      CHECK(type_parts.size() >= 1);
      CHECK(field_type_str_enum_map_->find(type_parts[0]) !=
            field_type_str_enum_map_->end())
          << "Unknown field type in schema file: " << parts[kTypeIdx];
      enum_field_types field_type =
          field_type_str_enum_map_->at(parts[kTypeIdx]);
      bool unsigned_flag = false;
      if (type_parts.size() > 1) {
        CHECK(type_parts.size() == 2);
        CHECK(type_parts[1] == "UNSIGNED");
        unsigned_flag = true;
      }

      char* end_ptr;
      int field_size = strtol(parts[kLengthIdx].c_str(), &end_ptr, 10);
      CHECK(*end_ptr == '\0') << "Invalid length in schema file:\n" << line;
      bool index_field;
      if (parts[kIndexIdx] == "true") {
        index_field = true;
        if (!requires_index_) {
          requires_index_ = true;
        }
      } else {
        CHECK(parts[kIndexIdx] == "false");
        index_field = false;
      }

    
      field_info_.insert(make_pair(
              fid, FieldInfo(field_type, field_size, index_field, 
                             unsigned_flag)));
      table_to_fields_[*table].push_back(fid);
    }
    fields_in_order_.push_back(field_ids);

  }
  CHECK(schema_data->eof()) << "Error reading schema before EOF";
  DCHECK(table_to_fields_.size() == all_tables_.size());
  DCHECK(field_name_to_ids_.size() == fields_in_order_.size());
}

const std::vector<FieldId>* Schema::GetFieldIdsForField(
    const std::string& field_name) const {
  DCHECK(field_name_to_ids_.find(field_name) != field_name_to_ids_.end());
  return &field_name_to_ids_.find(field_name)->second;
}

const vector<FieldId>* Schema::GetFieldIds(size_t i) const {
  DCHECK(i < fields_in_order_.size());
  return &fields_in_order_[i];
}

enum_field_types Schema::GetFieldType(const FieldId& fid) const {
  const FieldInfo& info = GetFieldInfo(fid);
  return info.type;
}


const FieldInfo& Schema::GetFieldInfo(const FieldId& field_id) const {
  DCHECK(field_info_.find(field_id) != field_info_.end());
  return field_info_.at(field_id);
}

std::map<std::string, enum_field_types>* Schema::field_type_str_enum_map_;
std::set<enum_field_types>* Schema::quoted_types_;
std::set<enum_field_types>* Schema::escaped_types_;

void InitializeSchemaStatics() {
  Schema::field_type_str_enum_map_ = new map<string, enum_field_types>;
  boost::assign::insert(*Schema::field_type_str_enum_map_)
      ("TINYINT", MYSQL_TYPE_TINY)("TINYINT UNSIGNED", MYSQL_TYPE_TINY)
			("SMALLINT", MYSQL_TYPE_SHORT)("SMALLINT UNSIGNED", MYSQL_TYPE_SHORT)
      ("INT", MYSQL_TYPE_LONG)("INT UNSIGNED", MYSQL_TYPE_LONG)
      ("BIGINT", MYSQL_TYPE_LONGLONG)("BIGINT UNSIGNED", MYSQL_TYPE_LONGLONG)
      ("FLOAT", MYSQL_TYPE_FLOAT)("FLOAT UNSIGNED", MYSQL_TYPE_FLOAT)
      ("DOUBLE", MYSQL_TYPE_DOUBLE)("DOUBLE UNSIGNED", MYSQL_TYPE_DOUBLE)
      ("DATE", MYSQL_TYPE_DATE)("TIME", MYSQL_TYPE_TIME)
      ("DATETIME", MYSQL_TYPE_DATETIME)("TEXT", MYSQL_TYPE_BLOB)
      ("CHAR", MYSQL_TYPE_STRING)("VARCHAR", MYSQL_TYPE_VAR_STRING)
      ("BLOB", MYSQL_TYPE_BLOB)("MEDIUMBLOB", MYSQL_TYPE_BLOB)
      ("ENUM", MYSQL_TYPE_STRING);

  Schema::quoted_types_ = new std::set<enum_field_types>;
  boost::assign::insert(*Schema::quoted_types_)
      (MYSQL_TYPE_TIME)(MYSQL_TYPE_DATE) (MYSQL_TYPE_DATETIME)
      (MYSQL_TYPE_STRING)(MYSQL_TYPE_VAR_STRING)(MYSQL_TYPE_BLOB);

  Schema::escaped_types_ = new std::set<enum_field_types>;
  boost::assign::insert(*Schema::escaped_types_)
      (MYSQL_TYPE_STRING)(MYSQL_TYPE_VAR_STRING)(MYSQL_TYPE_BLOB);
}

void FinalizeSchemaStatics() {
  delete Schema::field_type_str_enum_map_;
  delete Schema::quoted_types_;
  delete Schema::escaped_types_;
}

ADD_INITIALIZER("SchemaFieldTypeInit", &InitializeSchemaStatics);
ADD_FINALIZER("SchemaFieldTypeFinalize", &FinalizeSchemaStatics);
